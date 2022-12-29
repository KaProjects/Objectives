package org.kaleta.objectives.listener

import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.ValueEventListener
import org.kaleta.objectives.DataSource

class LabelsValueEventListener : ValueEventListener {

    override fun onDataChange(snapshot: DataSnapshot) {
        DataSource.labels.clear()
        DataSource.labelIds.clear()
        for (value in snapshot.children) {
            DataSource.labels.add(value.value as String)
            DataSource.labelIds.add(value.key!!)
        }
    }

    override fun onCancelled(error: DatabaseError) {

    }
}