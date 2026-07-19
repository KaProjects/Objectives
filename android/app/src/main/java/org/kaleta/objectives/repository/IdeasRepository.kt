package org.kaleta.objectives.repository

import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.ValueOption

interface IdeasRepository {
    fun observe(observer: Observer): ListenerRegistration

    fun addIdea(valueId: String, value: String, onComplete: OperationCallback)

    fun editIdea(valueId: String, ideaId: String, value: String, onComplete: OperationCallback)

    fun deleteIdea(valueId: String, ideaId: String, onComplete: OperationCallback)

    interface Observer {
        fun onValuesChanged(values: List<ValueOption>)

        fun onIdeasChanged(ideasByValue: Map<String, List<Idea>>)

        fun onError(error: Throwable)
    }

    fun interface ListenerRegistration {
        fun remove()
    }

    fun interface OperationCallback {
        fun onComplete(result: Result<Unit>)
    }
}
