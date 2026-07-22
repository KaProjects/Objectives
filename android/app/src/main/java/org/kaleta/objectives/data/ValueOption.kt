package org.kaleta.objectives.data

data class ValueOption(
    val id: String,
    val name: String,
) {
    override fun toString(): String = name
}
