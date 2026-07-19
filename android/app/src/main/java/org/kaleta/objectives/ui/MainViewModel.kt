package org.kaleta.objectives.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.MainUiState
import org.kaleta.objectives.data.ValueOption
import org.kaleta.objectives.repository.IdeasRepository

class MainViewModel(
    private val repository: IdeasRepository,
) : ViewModel() {
    private val mutableState = MutableLiveData(MainUiState())
    val state: LiveData<MainUiState> = mutableState

    private var values: List<ValueOption> = emptyList()
    private var ideasByValue: Map<String, List<Idea>> = emptyMap()
    private var selectedValueId: String? = null
    private var valuesLoaded = false
    private var ideasLoaded = false

    private val registration = repository.observe(object : IdeasRepository.Observer {
        override fun onValuesChanged(values: List<ValueOption>) {
            this@MainViewModel.values = values.toList()
            valuesLoaded = true
            selectedValueId = selectedValueId
                ?.takeIf { selectedId -> values.any { it.id == selectedId } }
                ?: values.firstOrNull()?.id
            publishState()
        }

        override fun onIdeasChanged(ideasByValue: Map<String, List<Idea>>) {
            this@MainViewModel.ideasByValue = ideasByValue.mapValues { (_, ideas) -> ideas.toList() }
            ideasLoaded = true
            publishState()
        }

        override fun onError(error: Throwable) {
            publishState(error.readableMessage())
        }
    })

    fun selectValue(valueId: String) {
        if (valueId == selectedValueId || values.none { it.id == valueId }) return
        selectedValueId = valueId
        publishState()
    }

    fun addIdea(value: String): Boolean {
        val selectedId = selectedValueId ?: return reject("Select a value first")
        val normalizedValue = value.trim()
        if (normalizedValue.isBlank()) return reject("Idea cannot be blank")

        repository.addIdea(selectedId, normalizedValue, ::handleOperationResult)
        return true
    }

    fun editIdea(idea: Idea, value: String): Boolean {
        val selectedId = selectedValueId ?: return reject("Select a value first")
        val normalizedValue = value.trim()
        if (normalizedValue.isBlank()) return reject("Idea cannot be blank")
        if (normalizedValue == idea.value) return true

        repository.editIdea(selectedId, idea.id, normalizedValue, ::handleOperationResult)
        return true
    }

    fun deleteIdea(idea: Idea) {
        val selectedId = selectedValueId
        if (selectedId == null) {
            reject("Select a value first")
            return
        }
        repository.deleteIdea(selectedId, idea.id, ::handleOperationResult)
    }

    fun clearError() {
        if (mutableState.value?.errorMessage == null) return
        publishState(errorMessage = null)
    }

    override fun onCleared() {
        registration.remove()
        super.onCleared()
    }

    private fun handleOperationResult(result: Result<Unit>) {
        result.exceptionOrNull()?.let { error -> publishState(error.readableMessage()) }
    }

    private fun reject(message: String): Boolean {
        publishState(message)
        return false
    }

    private fun publishState(errorMessage: String? = mutableState.value?.errorMessage) {
        mutableState.value = MainUiState(
            values = values,
            selectedValueId = selectedValueId,
            ideas = selectedValueId?.let { ideasByValue[it] }.orEmpty(),
            isLoading = !valuesLoaded || !ideasLoaded,
            errorMessage = errorMessage,
        )
    }

    private fun Throwable.readableMessage(): String = message?.takeIf(String::isNotBlank)
        ?: "Firebase operation failed"
}
