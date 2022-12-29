package org.kaleta.objectives

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import org.kaleta.objectives.listener.IdeasValueEventListener
import org.kaleta.objectives.listener.LabelsValueEventListener
import org.kaleta.objectives.ui.MainFragment

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        DataSource.ideasReference.addValueEventListener(IdeasValueEventListener())
        DataSource.labelsReference.addValueEventListener(LabelsValueEventListener())


        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.container, MainFragment.newInstance())
                .commitNow()
        }


    }
}