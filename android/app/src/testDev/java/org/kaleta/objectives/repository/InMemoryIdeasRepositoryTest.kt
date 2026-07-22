package org.kaleta.objectives.repository

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData
import org.kaleta.objectives.data.SubvalueOption
import org.kaleta.objectives.data.ValueOption

class InMemoryIdeasRepositoryTest {
    @Test
    fun `add edit and delete update only the selected subvalue`() {
        val repository = InMemoryIdeasRepository(
            IdeasData(
                values = listOf(ValueOption(id = "1", name = "Health")),
                subvaluesByValue = mapOf(
                    "1" to listOf(
                        SubvalueOption(id = "0", name = "default"),
                        SubvalueOption(id = "1", name = "Exercise"),
                    ),
                ),
                ideasByValueAndSubvalue = mapOf(
                    "1" to mapOf(
                        "0" to listOf(Idea(id = "idea-1", name = "Drink water", description = "")),
                        "1" to listOf(Idea(id = "idea-2", name = "Walk", description = "")),
                    ),
                ),
            ),
        )
        var latestData: IdeasData? = null
        repository.observe(object : IdeasRepository.Observer {
            override fun onDataChanged(data: IdeasData) {
                latestData = data
            }

            override fun onError(error: Throwable) = Unit
        })

        repository.addIdea("1", "1", "Stretch", "Before breakfast") { result -> assertTrue(result.isSuccess) }
        val addedIdea = latestData!!.ideasByValueAndSubvalue.getValue("1").getValue("1")
            .single { it.name == "Stretch" }
        repository.editIdea("1", "1", addedIdea, "Morning stretch", "Before breakfast") { result ->
            assertTrue(result.isSuccess)
        }
        repository.deleteIdea("1", "1", "idea-2") { result -> assertTrue(result.isSuccess) }

        assertEquals(
            listOf(Idea(id = addedIdea.id, name = "Morning stretch", description = "Before breakfast")),
            latestData!!.ideasByValueAndSubvalue.getValue("1").getValue("1"),
        )
        assertEquals(
            listOf("Drink water"),
            latestData!!.ideasByValueAndSubvalue.getValue("1").getValue("0").map(Idea::name),
        )
    }
}
