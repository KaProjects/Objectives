package org.kaleta.objectives.listener

import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.ValueEventListener
import org.kaleta.objectives.DataSource
import org.kaleta.objectives.data.Idea

class IdeasValueEventListener : ValueEventListener {

    override fun onDataChange(snapshot: DataSnapshot) {
        DataSource.ideasMap.clear()
        for (value in snapshot.children) {
            var ideas = ArrayList<Idea>()
            for (idea in value.children) {
                val ideaObj = Idea()
                ideaObj.value = idea.value as String
                ideaObj.id = idea.key!!
                ideas.add(ideaObj)
            }
            DataSource.ideasMap.put(value.key!!, ideas)
        }
    }

    override fun onCancelled(error: DatabaseError) {

    }
}