package org.kaleta.objectives.data

data class IdeasData(
    val values: List<ValueOption>,
    val subvaluesByValue: Map<String, List<SubvalueOption>>,
    val ideasByValueAndSubvalue: Map<String, Map<String, List<Idea>>>,
)
