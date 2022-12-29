package org.kaleta.objectives

import com.google.firebase.database.FirebaseDatabase
import org.kaleta.objectives.data.Idea
import java.util.*
import kotlin.collections.ArrayList
import kotlin.collections.HashMap

object DataSource {

    val database:FirebaseDatabase = FirebaseDatabase.getInstance()

    const val ideasPath = "ideas/"
    val ideasReference = database.getReference(ideasPath)
    var ideasMap: MutableMap<String, List<Idea>> = Collections.synchronizedMap(HashMap())

    const val labelsPath = "labels/"
    val labelsReference = database.getReference(labelsPath)
    var labels: ArrayList<String> = ArrayList()
    var labelIds: ArrayList<String> = ArrayList()

    init {

    }

    fun addIdea(valueId: String, ideaValue: String){
        ideasReference.child(valueId).push().setValue(ideaValue)
    }

    fun deleteIdea(valueId: String, ideaId: String){
        ideasReference.child(valueId).child(ideaId).removeValue()
    }

    fun editIdea(valueId: String, ideaId: String, newValue: String){
        ideasReference.child(valueId).child(ideaId).setValue(newValue)
    }
}