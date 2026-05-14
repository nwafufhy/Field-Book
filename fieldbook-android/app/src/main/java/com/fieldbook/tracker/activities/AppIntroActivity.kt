package com.fieldbook.tracker.activities

import android.content.Context
import android.content.res.Configuration
import android.graphics.Color
import android.os.Bundle
import androidx.activity.enableEdgeToEdge
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.preference.PreferenceManager
import com.fieldbook.tracker.R
import com.fieldbook.tracker.fragments.GallerySlideFragment
import com.fieldbook.tracker.fragments.OptionalSetupFragment
import com.fieldbook.tracker.fragments.RequiredSetupPolicyFragment
import com.fieldbook.tracker.preferences.PreferenceKeys
import com.github.appintro.AppIntro
import com.github.appintro.AppIntroFragment.Companion.createInstance
import java.util.Locale

class AppIntroActivity : AppIntro() {

    override fun attachBaseContext(newBase: Context) {
        val prefs = PreferenceManager.getDefaultSharedPreferences(newBase)
        val langTag = prefs.getString(PreferenceKeys.LANGUAGE_LOCALE_ID, "")?.ifEmpty { "zh-CN" } ?: "zh-CN"
        val locale = Locale.forLanguageTag(langTag)
        Locale.setDefault(locale)
        val config = Configuration(newBase.resources.configuration)
        config.setLocale(locale)
        super.attachBaseContext(newBase.createConfigurationContext(config))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // field book info 1
        addSlide(
            createInstance(
                getString(R.string.app_intro_intro_title_slide1),
                getString(R.string.app_intro_intro_summary_slide1),
                R.drawable.field_book_intro_icon,
                R.color.main_primary_transparent,
                R.color.main_color_text_dark,
                R.color.main_color_text_dark,
            )
        )

        // gallery slide
        addSlide(GallerySlideFragment.newInstance())

        // required setup slide
        addSlide(
            RequiredSetupPolicyFragment.newInstance(
                getString(R.string.app_intro_required_setup_title),
                getString(R.string.app_intro_required_setup_summary),
                R.color.main_primary_transparent
            )
        )

        // optional setup slide
        addSlide(
            OptionalSetupFragment.newInstance(
                getString(R.string.app_intro_required_optional_title),
                getString(R.string.app_intro_required_optional_summary),
                R.color.main_primary_transparent
            )
        )

        isSkipButtonEnabled = false

        setNextArrowColor(ContextCompat.getColor(this, R.color.main_primary_dark))
        setIndicatorColor(
            ContextCompat.getColor(this, R.color.main_primary_dark),
            ContextCompat.getColor(this, R.color.main_primary_transparent)
        )
        setColorDoneText(Color.BLACK)
    }

    override fun onDonePressed(currentFragment: Fragment?) {
        super.onDonePressed(currentFragment)
        setResult(RESULT_OK)
        finish()
    }
}