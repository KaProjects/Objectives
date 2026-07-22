package org.kaleta.objectives.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData
import org.kaleta.objectives.data.MainUiState
import org.kaleta.objectives.data.SubvalueOption
import org.kaleta.objectives.data.ValueOption
import org.kaleta.objectives.repository.IdeasRepository

class MainViewModel(
    private val repository: IdeasRepository,
) : ViewModel() {
    private val mutableState = MutableLiveData(MainUiState())
    val state: LiveData<MainUiState> = mutableState

    private var values: List<ValueOption> = emptyList()
    private var subvaluesByValue: Map<String, List<SubvalueOption>> = emptyMap()
    private var ideasByValueAndSubvalue: Map<String, Map<String, List<Idea>>> = emptyMap()
    private var selectedValueId: String? = null
    private var selectedSubvalueId: String? = null
    private var dataLoaded = false

    private val registration = repository.observe(object : IdeasRepository.Observer {
        override fun onDataChanged(data: IdeasData) {
            values = data.values.toList()
            subvaluesByValue = data.subvaluesByValue.mapValues { (_, subvalues) -> subvalues.toList() }
            ideasByValueAndSubvalue = data.ideasByValueAndSubvalue.mapValues { (_, subvalues) ->
                subvalues.mapValues { (_, ideas) -> ideas.toList() }
            }
            dataLoaded = true

            val currentValueId = selectedValueId
            selectedValueId = currentValueId
                ?.takeIf { valueId -> values.any { it.id == valueId } }
                ?: values.firstOrNull()?.id
            selectedSubvalueId = selectedSubvalueId
                ?.takeIf { subvalueId -> currentSubvalues().any { it.id == subvalueId } }
                ?: defaultSubvalueId()
            publishState()
        }

        override fun onError(error: Throwable) {
            publishState(error.readableMessage())
        }
    })

    fun selectValue(valueId: String) {
        if (valueId == selectedValueId || values.none { it.id == valueId }) return
        selectedValueId = valueId
        selectedSubvalueId = defaultSubvalueId()
        publishState()
    }

    fun selectSubvalue(subvalueId: String) {
        if (subvalueId == selectedSubvalueId || currentSubvalues().none { it.id == subvalueId }) return
        selectedSubvalueId = subvalueId
        publishState()
    }

    fun addIdea(name: String, description: String): Boolean {
        val selection = selectedIdsOrReject() ?: return false
        val normalizedName = name.trim()
        val normalizedDescription = description.trim()
        if (normalizedName.isBlank()) return reject("Idea cannot be blank")

        repository.addIdea(
            selection.valueId,
            selection.subvalueId,
            normalizedName,
            normalizedDescription,
            ::handleOperationResult,
        )
        return true
    }

    fun editIdea(idea: Idea, name: String, description: String): Boolean {
        val selection = selectedIdsOrReject() ?: return false
        val normalizedName = name.trim()
        val normalizedDescription = description.trim()
        if (normalizedName.isBlank()) return reject("Idea cannot be blank")
        if (normalizedName == idea.name && normalizedDescription == idea.description) return true

        repository.editIdea(
            selection.valueId,
            selection.subvalueId,
            idea,
            normalizedName,
            normalizedDescription,
            ::handleOperationResult,
        )
        return true
    }

    fun deleteIdea(idea: Idea) {
        val selection = selectedIdsOrReject() ?: return
        repository.deleteIdea(selection.valueId, selection.subvalueId, idea.id, ::handleOperationResult)
    }

    fun clearError() {
        if (mutableState.value?.errorMessage == null) return
        publishState(errorMessage = null)
    }

    override fun onCleared() {
        registration.remove()
        super.onCleared()
    }

    private fun selectedIdsOrReject(): SelectedIds? {
        val valueId = selectedValueId ?: run {
            reject("Select a value first")
            return null
        }
        val subvalueId = selectedSubvalueId ?: run {
            reject("Select a subvalue first")
            return null
        }
        return SelectedIds(valueId, subvalueId)
    }

    private fun currentSubvalues(): List<SubvalueOption> = selectedValueId
        ?.let { valueId -> subvaluesByValue[valueId] }
        .orEmpty()

    private fun defaultSubvalueId(): String? = currentSubvalues()
        .firstOrNull { it.id == DEFAULT_SUBVALUE_ID }
        ?.id
        ?: currentSubvalues().firstOrNull()?.id

    private fun handleOperationResult(result: Result<Unit>) {
        result.exceptionOrNull()?.let { error -> publishState(error.readableMessage()) }
    }

    private fun reject(message: String): Boolean {
        publishState(message)
        return false
    }

    private fun publishState(errorMessage: String? = mutableState.value?.errorMessage) {
        val subvalues = currentSubvalues()
        mutableState.value = MainUiState(
            values = values,
            selectedValueId = selectedValueId,
            subvalues = subvalues,
            selectedSubvalueId = selectedSubvalueId,
            ideas = selectedValueId
                ?.let { valueId -> selectedSubvalueId?.let { subvalueId -> ideasByValueAndSubvalue[valueId]?.get(subvalueId) } }
                .orEmpty(),
            isLoading = !dataLoaded,
            errorMessage = errorMessage,
        )
    }

    private fun Throwable.readableMessage(): String = message?.takeIf(String::isNotBlank)
        ?: "Firebase operation failed"

    private data class SelectedIds(val valueId: String, val subvalueId: String)

    private companion object {
        const val DEFAULT_SUBVALUE_ID = "0"
    }
}
