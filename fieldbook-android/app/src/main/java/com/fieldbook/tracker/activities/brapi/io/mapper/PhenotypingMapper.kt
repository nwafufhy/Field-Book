package com.fieldbook.tracker.activities.brapi.io.mapper

import android.content.Context
import com.fieldbook.tracker.brapi.service.BrAPIService
import com.fieldbook.tracker.brapi.service.BrAPIServiceV2.ADDITIONAL_INFO_OBSERVATION_LEVEL_NAMES
import com.fieldbook.tracker.objects.TraitObject
import com.fieldbook.tracker.utilities.CategoryJsonUtil
import com.fieldbook.tracker.utilities.SynonymsUtil
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import org.brapi.v2.model.pheno.BrAPIObservationVariable
import org.brapi.v2.model.pheno.BrAPIScale
import org.brapi.v2.model.pheno.BrAPIScaleValidValues
import org.brapi.v2.model.pheno.BrAPITrait
import org.brapi.v2.model.pheno.BrAPITraitDataType

/**
 * File for extension functions to convert BrAPI objects to FieldBook objects
 */

fun BrAPIObservationVariable.toTraitObject(context: Context) = TraitObject().also {

    it.defaultValue = defaultValue ?: ""
    it.name = observationVariableName
    it.alias = observationVariableName

    it.synonyms = SynonymsUtil.addAliasToSynonyms(observationVariableName, synonyms ?: emptyList())

    it.details = trait.traitDescription ?: ""
    it.externalDbId = observationVariableDbId

    BrAPIService.getHostUrl(context)?.let { url ->
        it.traitDataSource = url
    }

    scale?.validValues?.minimumValue?.let { min ->
        it.minimum = min.toString()
    }

    scale?.validValues?.maximumValue?.let { max ->
        it.maximum = max.toString()
    }

    val dataType = scale?.dataType
    it.format = if (dataType != null) {
        DataTypes.convertBrAPIDataType(dataType.brapiValue)
    } else {
        "text"
    }

    if (it.format == "multicat") { // convert brapi multicat to field book categorical
        it.format = "categorical"
        it.allowMulticat = true
    }

    scale?.validValues?.categories?.let { categories ->
        if (categories.isNotEmpty()) {
            it.categories = CategoryJsonUtil.buildCategoryList(categories)
            it.details += "\nCategories: ${CategoryJsonUtil.buildCategoryDescriptionString(categories)}"
        }
    }

    if (additionalInfo != null && additionalInfo.has(ADDITIONAL_INFO_OBSERVATION_LEVEL_NAMES)) {

        additionalInfo.getAsJsonArray(ADDITIONAL_INFO_OBSERVATION_LEVEL_NAMES)?.let { array ->

            val listType = object : TypeToken<List<String?>?>() {}.type

            it.observationLevelNames =
                Gson().fromJson<List<String>>(
                    array,
                    listType
                )

        }
    }

    it.visible = true

}

fun TraitObject.toBrAPIObservationVariable(): BrAPIObservationVariable {
    return BrAPIObservationVariable().apply {

        if (!externalDbId.isNullOrEmpty()) {
            observationVariableDbId = externalDbId
        }

        observationVariableName = name
        defaultValue = defaultValue.ifEmpty { null }

        if (synonyms.isNotEmpty()) {
            this.synonyms = synonyms.toList()
        }

        trait = BrAPITrait().apply {
            traitName = this@toBrAPIObservationVariable.name
            traitDescription = details.ifEmpty { null }
        }

        scale = BrAPIScale().apply {
            dataType = BrAPITraitDataType.fromValue(
                DataTypes.convertFieldBookFormatToBrAPIDataType(format)
            )

            val hasMin = this@toBrAPIObservationVariable.minimum.isNotEmpty()
            val hasMax = this@toBrAPIObservationVariable.maximum.isNotEmpty()
            val hasCat = this@toBrAPIObservationVariable.categories.isNotEmpty()

            if (hasMin || hasMax || hasCat) {
                validValues = BrAPIScaleValidValues().apply {
                    if (hasMin) minimumValue = this@toBrAPIObservationVariable.minimum
                    if (hasMax) maximumValue = this@toBrAPIObservationVariable.maximum
                    if (hasCat) categories = CategoryJsonUtil.decode(
                        this@toBrAPIObservationVariable.categories
                    )
                }
            }
        }
    }
}