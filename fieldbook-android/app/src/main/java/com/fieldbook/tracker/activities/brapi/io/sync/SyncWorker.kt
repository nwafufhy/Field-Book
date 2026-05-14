package com.fieldbook.tracker.activities.brapi.io.sync

import android.content.Context
import android.util.Log
import androidx.preference.PreferenceManager
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.fieldbook.tracker.activities.brapi.io.mapper.toBrAPIObservationVariable
import com.fieldbook.tracker.brapi.model.FieldBookImage
import com.fieldbook.tracker.brapi.service.BrAPIService
import com.fieldbook.tracker.brapi.service.BrAPIServiceFactory
import com.fieldbook.tracker.database.DataHelper
import com.fieldbook.tracker.database.dao.ObservationVariableDao
import com.fieldbook.tracker.database.dao.StudyDao
import com.fieldbook.tracker.preferences.PreferenceKeys
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

class SyncWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    companion object {
        private const val TAG = "SyncWorker"
    }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val prefs = PreferenceManager.getDefaultSharedPreferences(applicationContext)

        if (!prefs.getBoolean(PreferenceKeys.BRAPI_SYNC_ENABLED, false)) {
            Log.d(TAG, "Sync disabled, skipping")
            return@withContext Result.success()
        }

        val baseUrl = prefs.getString(PreferenceKeys.BRAPI_BASE_URL, null)
        if (baseUrl.isNullOrBlank()) {
            Log.d(TAG, "No BrAPI base URL, skipping")
            return@withContext Result.success()
        }

        try {
            val dataHelper = DataHelper(applicationContext)
            val brAPIService = BrAPIServiceFactory.getBrAPIService(applicationContext)
            val hostUrl = BrAPIService.getHostUrl(applicationContext) ?: "unknown"
            val fields = StudyDao.getAllFieldObjects("study_name")

            if (fields.isEmpty()) {
                Log.d(TAG, "No fields to sync")
                return@withContext Result.success()
            }

            var totalUploaded = 0
            var totalDownloaded = 0
            var totalDownloadedImages = 0

            for (field in fields) {
                val fieldId = field.studyId
                val exportData = dataHelper.getBrAPIExportData(fieldId, hostUrl)

                // ── Upload variable definitions for user-created traits ──
                val newObsForUpload = (exportData["newObservations"] ?: emptyList()) +
                                      (exportData["userCreatedTraitObservations"] ?: emptyList()) +
                                      (exportData["newImageObservations"] ?: emptyList()) +
                                      (exportData["userCreatedImageObservations"] ?: emptyList())
                val localTraits = collectLocalTraitsFromObservations(newObsForUpload)
                if (localTraits.isNotEmpty()) {
                    try {
                        val brapiVariables = localTraits.map { it.toBrAPIObservationVariable() }
                        val created = brAPIService.awaitCreateVariables(brapiVariables)
                        for (brapiVar in created) {
                            val varName = brapiVar.observationVariableName
                            val serverId = brapiVar.observationVariableDbId
                            if (varName != null && serverId != null) {
                                val trait = localTraits.find { it.name == varName }
                                if (trait != null) {
                                    ObservationVariableDao.updateExternalDbId(
                                        trait.id, serverId, hostUrl
                                    )
                                }
                            }
                        }
                        Log.d(TAG, "Uploaded ${created.size} variable definitions")
                    } catch (e: Exception) {
                        Log.e(TAG, "Variable upload failed, continuing", e)
                    }
                }

                // ── Upload new observations (BrAPI + user-created traits + images) ──
                if (newObsForUpload.isNotEmpty()) {
                    val uploaded = mutableListOf<Int>()
                    brAPIService.awaitCreateObservations(
                        applicationContext, newObsForUpload,
                        onChunkCompleted = { chunk -> synchronized(uploaded) { uploaded.add(chunk.size) } },
                        onChunkFailed = { code, _ -> Log.e(TAG, "Upload failed: $code") },
                    )
                    totalUploaded += uploaded.sum()
                }

                // ── Upload edited observations (including images) ──
                val editedObs = (exportData["editedObservations"] ?: emptyList()) +
                                (exportData["editedImageObservations"] ?: emptyList())
                if (editedObs.isNotEmpty()) {
                    val uploaded = mutableListOf<Int>()
                    brAPIService.awaitUpdateObservations(
                        applicationContext, editedObs,
                        onChunkCompleted = { chunk -> synchronized(uploaded) { uploaded.add(chunk.size) } },
                        onChunkFailed = { code, _ -> Log.e(TAG, "Update failed: $code") },
                    )
                    totalUploaded += uploaded.sum()
                }

                // ── Upload new images (metadata + content) ──
                val newImageObs = (exportData["newImageObservations"] ?: emptyList()) +
                                  (exportData["userCreatedImageObservations"] ?: emptyList())
                if (newImageObs.isNotEmpty()) {
                    val images = dataHelper.getImageDetails(applicationContext, newImageObs)
                    for (image in images) {
                        try {
                            val imageWithId = brAPIService.awaitPostImageMetaData(image)
                            imageWithId.loadImage(applicationContext)
                            brAPIService.awaitPutImageContent(imageWithId)
                            totalUploaded++
                        } catch (e: Exception) {
                            Log.e(TAG, "Image upload failed: ${image.fileName}", e)
                        }
                    }
                }

                // ── Upload edited images (update metadata + content, including incomplete) ──
                val editedImageObs = (exportData["editedImageObservations"] ?: emptyList()) +
                                     (exportData["incompleteImageObservations"] ?: emptyList())
                if (editedImageObs.isNotEmpty()) {
                    val images = dataHelper.getImageDetails(applicationContext, editedImageObs)
                    for (image in images) {
                        try {
                            image.loadImage(applicationContext)
                            brAPIService.awaitPutImage(image)
                            brAPIService.awaitPutImageContent(image)
                            totalUploaded++
                        } catch (e: Exception) {
                            Log.e(TAG, "Image update failed: ${image.fileName}", e)
                        }
                    }
                }

                // ── Download: get latest observations for this study ──
                val unitIdsForImages = mutableListOf<String>()
                try {
                    val paginationManager = com.fieldbook.tracker.brapi.service.BrapiPaginationManager(0, 100)
                    val page = brAPIService.awaitGetSingleObservationPage(
                        fieldId.toString(), emptyList(), paginationManager
                    )
                    totalDownloaded += page.size
                    for (obs in page) {
                        if (obs.dbId != null) {
                            try {
                                dataHelper.insertObservation(
                                    obs.unitDbId ?: "",
                                    obs.variableDbId ?: "",
                                    obs.value ?: "",
                                    obs.collector ?: "",
                                    "", "", // location, notes
                                    fieldId.toString(),
                                    obs.dbId,
                                    obs.timestamp,
                                    obs.lastSyncedTime,
                                    obs.rep ?: "0",
                                )
                            } catch (_: Exception) {}
                        }
                        obs.unitDbId?.let { unitIdsForImages.add(it) }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Download failed for field $fieldId", e)
                }

                // ── Download images for this field ──
                try {
                    val uniqueUnitIds = unitIdsForImages.distinct()
                    for (unitId in uniqueUnitIds) {
                        try {
                            val images = brAPIService.awaitGetImages(unitId)
                            for (img in images) {
                                val imgDbId = img.dbId ?: continue
                                val imageContent = brAPIService.awaitGetImageContent(imgDbId)
                                val imageData = imageContent.imageData
                                if (imageData != null) {
                                    val dir = java.io.File(applicationContext.filesDir, "plot_data")
                                    dir.mkdirs()
                                    val fileName = img.fileName ?: imgDbId
                                    val file = java.io.File(dir, fileName)
                                    file.writeBytes(imageData)
                                    totalDownloadedImages++
                                }
                            }
                        } catch (_: Exception) {}
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Image download failed for field $fieldId", e)
                }
            }

            // Update last sync time
            val now = OffsetDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)
            prefs.edit().putString(PreferenceKeys.BRAPI_LAST_SYNC_TIME, now).apply()

            if (totalUploaded > 0 || totalDownloaded > 0 || totalDownloadedImages > 0) {
                SyncNotifications.showSyncComplete(
                    applicationContext, totalUploaded, totalDownloaded, 0, totalDownloadedImages
                )
            }

            Log.d(TAG, "Sync done: $totalUploaded up, $totalDownloaded down, $totalDownloadedImages img")
            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Sync error", e)
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }
}
