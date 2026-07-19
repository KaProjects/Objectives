package org.kaleta.objectives.data

data class MainUiState(
    val values: List<ValueOption> = emptyList(),
    val selectedValueId: String? = null,
    val subvalues: List<SubvalueOption> = emptyList(),
    val selectedSubvalueId: String? = null,
    val ideas: List<Idea> = emptyList(),
    val isLoading: Boolean = true,
    val errorMessage: String? = null,
) {
    val selectedValue: ValueOption?
        get() = values.firstOrNull { it.id == selectedValueId }

    val selectedSubvalue: SubvalueOption?
        get() = subvalues.firstOrNull { it.id == selectedSubvalueId }
}
