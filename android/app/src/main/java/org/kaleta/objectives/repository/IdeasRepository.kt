package org.kaleta.objectives.repository

import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData

interface IdeasRepository {
    fun observe(observer: Observer): ListenerRegistration

    fun addIdea(
        valueId: String,
        subvalueId: String,
        name: String,
        description: String,
        onComplete: OperationCallback,
    )

    fun editIdea(
        valueId: String,
        subvalueId: String,
        idea: Idea,
        name: String,
        description: String,
        onComplete: OperationCallback,
    )

    fun deleteIdea(valueId: String, subvalueId: String, ideaId: String, onComplete: OperationCallback)

    interface Observer {
        fun onDataChanged(data: IdeasData)

        fun onError(error: Throwable)
    }

    fun interface ListenerRegistration {
        fun remove()
    }

    fun interface OperationCallback {
        fun onComplete(result: Result<Unit>)
    }
}
