package org.kaleta.objectives.repository

import com.google.android.gms.tasks.Task
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.database.ValueEventListener
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.ValueOption

class LegacyFirebaseIdeasRepository(
    database: FirebaseDatabase = FirebaseDatabase.getInstance(),
) : IdeasRepository {
    private val ideasReference = database.getReference(IDEAS_PATH)
    private val labelsReference = database.getReference(LABELS_PATH)

    override fun observe(observer: IdeasRepository.Observer): IdeasRepository.ListenerRegistration {
        val ideasListener = object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                observer.onIdeasChanged(snapshot.toIdeasByValue())
            }

            override fun onCancelled(error: DatabaseError) {
                observer.onError(error.toException())
            }
        }
        val labelsListener = object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                observer.onValuesChanged(snapshot.toValueOptions())
            }

            override fun onCancelled(error: DatabaseError) {
                observer.onError(error.toException())
            }
        }

        ideasReference.addValueEventListener(ideasListener)
        labelsReference.addValueEventListener(labelsListener)

        return IdeasRepository.ListenerRegistration {
            ideasReference.removeEventListener(ideasListener)
            labelsReference.removeEventListener(labelsListener)
        }
    }

    override fun addIdea(
        valueId: String,
        value: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        ideasReference.child(valueId).push().setValue(value).completeWith(onComplete)
    }

    override fun editIdea(
        valueId: String,
        ideaId: String,
        value: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        ideasReference.child(valueId).child(ideaId).setValue(value).completeWith(onComplete)
    }

    override fun deleteIdea(
        valueId: String,
        ideaId: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        ideasReference.child(valueId).child(ideaId).removeValue().completeWith(onComplete)
    }

    private fun DataSnapshot.toIdeasByValue(): Map<String, List<Idea>> = children
        .mapNotNull { valueSnapshot ->
            val valueId = valueSnapshot.key ?: return@mapNotNull null
            val ideas = valueSnapshot.children.mapNotNull { ideaSnapshot ->
                val ideaId = ideaSnapshot.key ?: return@mapNotNull null
                val value = ideaSnapshot.getValue(String::class.java) ?: return@mapNotNull null
                Idea(id = ideaId, value = value)
            }
            valueId to ideas
        }
        .toMap()

    private fun DataSnapshot.toValueOptions(): List<ValueOption> = children.mapNotNull { snapshot ->
        val id = snapshot.key ?: return@mapNotNull null
        val name = snapshot.getValue(String::class.java) ?: return@mapNotNull null
        ValueOption(id = id, name = name)
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
        const val IDEAS_PATH = "ideas"
        const val LABELS_PATH = "labels"
    }
}
