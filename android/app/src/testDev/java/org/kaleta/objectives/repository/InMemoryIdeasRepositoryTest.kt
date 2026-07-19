package org.kaleta.objectives.repository

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.ValueOption

class InMemoryIdeasRepositoryTest {
    @Test
    fun `add edit and delete update dev ideas without Firebase`() {
        val repository = InMemoryIdeasRepository(
            DevIdeasData(
                values = listOf(ValueOption(id = "1", name = "Health")),
                ideasByValue = mapOf("1" to listOf(Idea(id = "idea-1", value = "Walk"))),
            ),
        )
        var latestIdeas: Map<String, List<Idea>> = emptyMap()
        repository.observe(object : IdeasRepository.Observer {
            override fun onValuesChanged(values: List<ValueOption>) = Unit

            override fun onIdeasChanged(ideasByValue: Map<String, List<Idea>>) {
                latestIdeas = ideasByValue
            }

            override fun onError(error: Throwable) = Unit
        })

        repository.addIdea("1", "Stretch") { result -> assertTrue(result.isSuccess) }
        val addedIdea = latestIdeas.getValue("1").single { it.value == "Stretch" }

        repository.editIdea("1", addedIdea.id, "Morning stretch") { result ->
            assertTrue(result.isSuccess)
        }
        repository.deleteIdea("1", "idea-1") { result -> assertTrue(result.isSuccess) }

        assertEquals(listOf("Morning stretch"), latestIdeas.getValue("1").map(Idea::value))
    }
}
