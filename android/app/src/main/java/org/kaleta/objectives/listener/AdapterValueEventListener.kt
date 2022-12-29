package org.kaleta.objectives.listener

import android.widget.ArrayAdapter
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.ValueEventListener

class AdapterValueEventListener(adapter: ArrayAdapter<String>) : ValueEventListener {

    private var adapter: ArrayAdapter<String>

    init {
        this.adapter = adapter
    }
    override fun onDataChange(snapshot: DataSnapshot) {
        adapter.notifyDataSetChanged();
    }

    override fun onCancelled(error: DatabaseError) {

    }
}