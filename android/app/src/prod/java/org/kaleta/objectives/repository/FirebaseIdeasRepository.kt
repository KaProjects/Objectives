package org.kaleta.objectives.repository

import com.google.android.gms.tasks.Task
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.database.ValueEventListener
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData
import org.kaleta.objectives.data.SubvalueOption
import org.kaleta.objectives.data.ValueOption

class FirebaseIdeasRepository(
    database: FirebaseDatabase = FirebaseDatabase.getInstance(),
) : IdeasRepository {
    private val valuesReference = database.getReference(VALUES_PATH)

    override fun observe(observer: IdeasRepository.Observer): IdeasRepository.ListenerRegistration {
        val listener = object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                observer.onDataChanged(snapshot.toIdeasData())
            }

            override fun onCancelled(error: DatabaseError) {
                observer.onError(error.toException())
            }
        }
        valuesReference.addValueEventListener(listener)

        return IdeasRepository.ListenerRegistration {
            valuesReference.removeEventListener(listener)
        }
    }

    override fun addIdea(
        valueId: String,
        subvalueId: String,
        name: String,
        description: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        ideasReference(valueId, subvalueId)
            .push()
            .setValue(mapOf("name" to name, "description" to description))
            .completeWith(onComplete)
    }

    override fun editIdea(
        valueId: String,
        subvalueId: String,
        idea: Idea,
        name: String,
        description: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        ideasReference(valueId, subvalueId)
            .child(idea.id)
            .setValue(mapOf("name" to name, "description" to description))
            .completeWith(onComplete)
    }

    override fun deleteIdea(
        valueId: String,
        subvalueId: String,
        ideaId: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        ideasReference(valueId, subvalueId).child(ideaId).removeValue().completeWith(onComplete)
    }

    private fun ideasReference(valueId: String, subvalueId: String) = valuesReference
        .child(valueId)
        .child(SUBVALUES_PATH)
        .child(subvalueId)
        .child(IDEAS_PATH)

    private fun DataSnapshot.toIdeasData(): IdeasData {
        val values = mutableListOf<ValueOption>()
        val subvaluesByValue = mutableMapOf<String, List<SubvalueOption>>()
        val ideasByValueAndSubvalue = mutableMapOf<String, Map<String, List<Idea>>>()

        children.forEach { valueSnapshot ->
            val valueId = valueSnapshot.key ?: return@forEach
            val valueName = valueSnapshot.child(NAME_FIELD).getValue(String::class.java) ?: return@forEach
            val subvalues = mutableListOf<SubvalueOption>()
            val ideasBySubvalue = mutableMapOf<String, List<Idea>>()

            valueSnapshot.child(SUBVALUES_PATH).children.forEach { subvalueSnapshot ->
                val subvalueId = subvalueSnapshot.key ?: return@forEach
                val subvalueName = subvalueSnapshot.child(NAME_FIELD).getValue(String::class.java)
                    ?: return@forEach
                subvalues += SubvalueOption(id = subvalueId, name = subvalueName)
                ideasBySubvalue[subvalueId] = subvalueSnapshot.child(IDEAS_PATH).children.mapNotNull { ideaSnapshot ->
                    val ideaId = ideaSnapshot.key ?: return@mapNotNull null
                    val name = ideaSnapshot.child(NAME_FIELD).getValue(String::class.java) ?: return@mapNotNull null
                    val description = ideaSnapshot.child(DESCRIPTION_FIELD).getValue(String::class.java).orEmpty()
                    Idea(id = ideaId, name = name, description = description)
                }
            }

            values += ValueOption(id = valueId, name = valueName)
            subvaluesByValue[valueId] = subvalues
            ideasByValueAndSubvalue[valueId] = ideasBySubvalue
        }

        return IdeasData(values, subvaluesByValue, ideasByValueAndSubvalue)
    }

    private fun Task<Void>.completeWith(callback: IdeasRepository.OperationCallback) {
        addOnCompleteListener { task ->
            if (task.isSuccessful) {
                callback.onComplete(Result.success(Unit))
            } else {
                callback.onComplete(
                    Result.failure(task.exception ?: IllegalStateException("Firebase operation failed")),
                )
            }
        }
    }

    private companion object {
        const val VALUES_PATH = "values"
        const val SUBVALUES_PATH = "subvalues"
        const val IDEAS_PATH = "ideas"
        const val NAME_FIELD = "name"
        const val DESCRIPTION_FIELD = "description"
    }
}
