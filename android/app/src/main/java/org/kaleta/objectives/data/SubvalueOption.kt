package org.kaleta.objectives.data

data class SubvalueOption(
    val id: String,
    val name: String,
) {
    val displayName: String
        get() = if (id == DEFAULT_SUBVALUE_ID) "-" else name

    override fun toString(): String = displayName

    private companion object {
        const val DEFAULT_SUBVALUE_ID = "0"
    }
}
