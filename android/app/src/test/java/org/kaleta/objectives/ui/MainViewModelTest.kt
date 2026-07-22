package org.kaleta.objectives.ui

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData
import org.kaleta.objectives.data.SubvalueOption
import org.kaleta.objectives.data.ValueOption
import org.kaleta.objectives.repository.IdeasRepository

class MainViewModelTest {
    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private lateinit var repository: FakeIdeasRepository
    private lateinit var viewModel: MainViewModel

    @Before
    fun setUp() {
        repository = FakeIdeasRepository()
        viewModel = MainViewModel(repository)
    }

    @Test
    fun `first value and its default subvalue are selected when data loads`() {
        val firstIdea = Idea(id = "idea-1", name = "First idea", description = "")
        repository.emit(data(ideas = mapOf("1" to mapOf("0" to listOf(firstIdea)))))

        val state = requireNotNull(viewModel.state.value)
        assertEquals("1", state.selectedValueId)
        assertEquals("0", state.selectedSubvalueId)
        assertEquals(listOf(firstIdea), state.ideas)
        assertFalse(state.isLoading)
    }

    @Test
    fun `selecting a value resets selection to default subvalue`() {
        repository.emit(data())
        viewModel.selectValue("1")
        viewModel.selectSubvalue("1")

        viewModel.selectValue("2")

        assertEquals("2", viewModel.state.value?.selectedValueId)
        assertEquals("0", viewModel.state.value?.selectedSubvalueId)
    }

    @Test
    fun `selecting a subvalue exposes only its ideas`() {
        val exerciseIdea = Idea(id = "idea-2", name = "Walk", description = "After lunch")
        repository.emit(
            data(
                ideas = mapOf(
                    "1" to mapOf(
                        "0" to listOf(Idea(id = "idea-1", name = "Drink water", description = "")),
                        "1" to listOf(exerciseIdea),
                    ),
                ),
            ),
        )

        viewModel.selectSubvalue("1")

        assertEquals("1", viewModel.state.value?.selectedSubvalueId)
        assertEquals(listOf(exerciseIdea), viewModel.state.value?.ideas)
    }

    @Test
    fun `empty values produce an empty safe state`() {
        repository.emit(IdeasData(emptyList(), emptyMap(), emptyMap()))

        val state = requireNotNull(viewModel.state.value)
        assertNull(state.selectedValueId)
        assertNull(state.selectedSubvalueId)
        assertTrue(state.ideas.isEmpty())
        assertFalse(state.isLoading)
    }

    @Test
    fun `blank idea is rejected without writing`() {
        repository.emit(data())

        val accepted = viewModel.addIdea("   ", "Optional description")

        assertFalse(accepted)
        assertTrue(repository.addRequests.isEmpty())
        assertEquals("Idea cannot be blank", viewModel.state.value?.errorMessage)
    }

    @Test
    fun `unchanged edit does not write`() {
        val idea = Idea(id = "idea-1", name = "Walk", description = "")
        repository.emit(data())

        val accepted = viewModel.editIdea(idea, " Walk ", "")

        assertTrue(accepted)
        assertTrue(repository.editRequests.isEmpty())
    }

    @Test
    fun `write failure is exposed as readable UI state`() {
        repository.nextOperationResult = Result.failure(IllegalStateException("Permission denied"))
        repository.emit(data())

        viewModel.addIdea("Walk", "")

        assertEquals("Permission denied", viewModel.state.value?.errorMessage)
    }

    @Test
    fun `editing description writes the selected value and subvalue`() {
        val idea = Idea(id = "idea-7", name = "Stretch", description = "")
        repository.emit(data())
        viewModel.selectSubvalue("1")

        val accepted = viewModel.editIdea(idea, "Stretch", "After a walk")

        assertTrue(accepted)
        assertEquals(
            listOf(EditRequest("1", "1", "idea-7", "Stretch", "After a walk")),
            repository.editRequests,
        )
    }

    @Test
    fun `adding an idea writes its description`() {
        repository.emit(data())

        val accepted = viewModel.addIdea("Walk", "After lunch")

        assertTrue(accepted)
        assertEquals(listOf(AddRequest("1", "0", "Walk", "After lunch")), repository.addRequests)
    }

    @Test
    fun `delete uses the selected value and subvalue`() {
        val idea = Idea(id = "idea-7", name = "Stretch", description = "")
        repository.emit(data())
        viewModel.selectSubvalue("1")

        viewModel.deleteIdea(idea)

        assertEquals(listOf(DeleteRequest("1", "1", "idea-7")), repository.deleteRequests)
    }

    private fun data(
        ideas: Map<String, Map<String, List<Idea>>> = emptyMap(),
    ) = IdeasData(
        values = listOf(
            ValueOption(id = "1", name = "Health"),
            ValueOption(id = "2", name = "Learning"),
        ),
        subvaluesByValue = mapOf(
            "1" to listOf(
                SubvalueOption(id = "0", name = "default"),
                SubvalueOption(id = "1", name = "Exercise"),
            ),
            "2" to listOf(SubvalueOption(id = "0", name = "default")),
        ),
        ideasByValueAndSubvalue = ideas,
    )

    private class FakeIdeasRepository : IdeasRepository {
        lateinit var observer: IdeasRepository.Observer
        val addRequests = mutableListOf<AddRequest>()
        val editRequests = mutableListOf<EditRequest>()
        val deleteRequests = mutableListOf<DeleteRequest>()
        var nextOperationResult: Result<Unit> = Result.success(Unit)

        override fun observe(observer: IdeasRepository.Observer): IdeasRepository.ListenerRegistration {
            this.observer = observer
            return IdeasRepository.ListenerRegistration { }
        }

        override fun addIdea(
            valueId: String,
            subvalueId: String,
            name: String,
            description: String,
            onComplete: IdeasRepository.OperationCallback,
        ) {
            addRequests += AddRequest(valueId, subvalueId, name, description)
            onComplete.onComplete(nextOperationResult)
        }

        override fun editIdea(
            valueId: String,
            subvalueId: String,
            idea: Idea,
            name: String,
            description: String,
            onComplete: IdeasRepository.OperationCallback,
        ) {
            editRequests += EditRequest(valueId, subvalueId, idea.id, name, description)
            onComplete.onComplete(nextOperationResult)
        }

        override fun deleteIdea(
            valueId: String,
            subvalueId: String,
            ideaId: String,
            onComplete: IdeasRepository.OperationCallback,
        ) {
            deleteRequests += DeleteRequest(valueId, subvalueId, ideaId)
            onComplete.onComplete(nextOperationResult)
        }

        fun emit(data: IdeasData) = observer.onDataChanged(data)
    }

    private data class AddRequest(
        val valueId: String,
        val subvalueId: String,
        val name: String,
        val description: String,
    )
    private data class EditRequest(
        val valueId: String,
        val subvalueId: String,
        val ideaId: String,
        val name: String,
        val description: String,
    )
    private data class DeleteRequest(val valueId: String, val subvalueId: String, val ideaId: String)
}
