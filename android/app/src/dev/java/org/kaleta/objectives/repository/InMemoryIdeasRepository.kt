package org.kaleta.objectives.repository

import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.ValueOption

class InMemoryIdeasRepository(initialData: DevIdeasData) : IdeasRepository {
    private val values = initialData.values.toList()
    private val ideasByValue = initialData.ideasByValue.mapValues { (_, ideas) -> ideas.toMutableList() }.toMutableMap()
    private val observers = mutableSetOf<IdeasRepository.Observer>()
    private var nextIdeaNumber = ideasByValue.values.flatten().size + 1

    override fun observe(observer: IdeasRepository.Observer): IdeasRepository.ListenerRegistration {
        observers += observer
        observer.onValuesChanged(values)
        observer.onIdeasChanged(snapshotIdeas())

        return IdeasRepository.ListenerRegistration {
            observers -= observer
        }
    }

    override fun addIdea(
        valueId: String,
        value: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        val ideas = ideasByValue[valueId]
        if (ideas == null) {
            onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown value: $valueId")))
            return
        }

        ideas += Idea(id = "dev-idea-${nextIdeaNumber++}", value = value)
        notifyIdeasChanged()
        onComplete.onComplete(Result.success(Unit))
    }

    override fun editIdea(
        valueId: String,
        ideaId: String,
        value: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        val ideas = ideasByValue[valueId]
        if (ideas == null) {
            onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown idea: $ideaId")))
            return
        }

        val index = ideas.indexOfFirst { it.id == ideaId }
        if (index < 0) {
            onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown idea: $ideaId")))
            return
        }

        ideas[index] = Idea(id = ideaId, value = value)
        notifyIdeasChanged()
        onComplete.onComplete(Result.success(Unit))
    }

    override fun deleteIdea(
        valueId: String,
        ideaId: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        val ideas = ideasByValue[valueId]
        val removed = ideas?.removeAll { it.id == ideaId } == true
        if (!removed) {
            onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown idea: $ideaId")))
            return
        }

        notifyIdeasChanged()
        onComplete.onComplete(Result.success(Unit))
    }

    private fun notifyIdeasChanged() {
        val snapshot = snapshotIdeas()
        observers.forEach { observer -> observer.onIdeasChanged(snapshot) }
    }

    private fun snapshotIdeas(): Map<String, List<Idea>> = ideasByValue
        .mapValues { (_, ideas) -> ideas.toList() }
        .toMap()
}
