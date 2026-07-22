package org.kaleta.objectives.repository

import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData

class InMemoryIdeasRepository(initialData: IdeasData) : IdeasRepository {
    private val data = initialData.toMutableData()
    private val observers = mutableSetOf<IdeasRepository.Observer>()
    private var nextIdeaNumber = data.ideasByValueAndSubvalue.values
        .flatMap { it.values }
        .flatten()
        .size + 1

    override fun observe(observer: IdeasRepository.Observer): IdeasRepository.ListenerRegistration {
        observers += observer
        observer.onDataChanged(data.snapshot())

        return IdeasRepository.ListenerRegistration {
            observers -= observer
        }
    }

    override fun addIdea(
        valueId: String,
        subvalueId: String,
        name: String,
        description: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        val ideas = ideasFor(valueId, subvalueId) ?: return unknownSubvalue(valueId, subvalueId, onComplete)
        ideas += Idea(id = "dev-idea-${nextIdeaNumber++}", name = name, description = description)
        notifyDataChanged()
        onComplete.onComplete(Result.success(Unit))
    }

    override fun editIdea(
        valueId: String,
        subvalueId: String,
        idea: Idea,
        name: String,
        description: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        val ideas = ideasFor(valueId, subvalueId) ?: return unknownSubvalue(valueId, subvalueId, onComplete)
        val index = ideas.indexOfFirst { it.id == idea.id }
        if (index < 0) {
            onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown idea: ${idea.id}")))
            return
        }

        ideas[index] = idea.copy(name = name, description = description)
        notifyDataChanged()
        onComplete.onComplete(Result.success(Unit))
    }

    override fun deleteIdea(
        valueId: String,
        subvalueId: String,
        ideaId: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        val ideas = ideasFor(valueId, subvalueId) ?: return unknownSubvalue(valueId, subvalueId, onComplete)
        if (!ideas.removeAll { it.id == ideaId }) {
            onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown idea: $ideaId")))
            return
        }

        notifyDataChanged()
        onComplete.onComplete(Result.success(Unit))
    }

    private fun ideasFor(valueId: String, subvalueId: String): MutableList<Idea>? = data
        .ideasByValueAndSubvalue[valueId]
        ?.get(subvalueId)

    private fun unknownSubvalue(
        valueId: String,
        subvalueId: String,
        onComplete: IdeasRepository.OperationCallback,
    ) {
        onComplete.onComplete(Result.failure(IllegalArgumentException("Unknown subvalue: $valueId/$subvalueId")))
    }

    private fun notifyDataChanged() {
        val snapshot = data.snapshot()
        observers.forEach { observer -> observer.onDataChanged(snapshot) }
    }

    private fun IdeasData.toMutableData() = MutableIdeasData(
        values = values.toList(),
        subvaluesByValue = subvaluesByValue.mapValues { (_, subvalues) -> subvalues.toList() }.toMutableMap(),
        ideasByValueAndSubvalue = ideasByValueAndSubvalue.mapValues { (_, subvalues) ->
            subvalues.mapValues { (_, ideas) -> ideas.toMutableList() }.toMutableMap()
        }.toMutableMap(),
    )

    private data class MutableIdeasData(
        val values: List<org.kaleta.objectives.data.ValueOption>,
        val subvaluesByValue: MutableMap<String, List<org.kaleta.objectives.data.SubvalueOption>>,
        val ideasByValueAndSubvalue: MutableMap<String, MutableMap<String, MutableList<Idea>>>,
    ) {
        fun snapshot() = IdeasData(
            values = values,
            subvaluesByValue = subvaluesByValue.mapValues { (_, subvalues) -> subvalues.toList() },
            ideasByValueAndSubvalue = ideasByValueAndSubvalue.mapValues { (_, subvalues) ->
                subvalues.mapValues { (_, ideas) -> ideas.toList() }
            },
        )
    }
}
