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
    fun `first value is selected when data loads`() {
        val firstIdea = Idea(id = "idea-1", value = "First idea")

        repository.emitIdeas(mapOf("1" to listOf(firstIdea)))
        repository.emitValues(
            listOf(
                ValueOption(id = "1", name = "Health"),
                ValueOption(id = "2", name = "Learning"),
            ),
        )

        val state = requireNotNull(viewModel.state.value)
        assertEquals("1", state.selectedValueId)
        assertEquals(listOf(firstIdea), state.ideas)
        assertFalse(state.isLoading)
    }

    @Test
    fun `selecting a value exposes only its ideas`() {
        val secondIdea = Idea(id = "idea-2", value = "Read a book")
        repository.emitIdeas(
            mapOf(
                "1" to listOf(Idea(id = "idea-1", value = "Walk")),
                "2" to listOf(secondIdea),
            ),
        )
        repository.emitValues(
            listOf(
                ValueOption(id = "1", name = "Health"),
                ValueOption(id = "2", name = "Learning"),
            ),
        )

        viewModel.selectValue("2")

        assertEquals("2", viewModel.state.value?.selectedValueId)
        assertEquals(listOf(secondIdea), viewModel.state.value?.ideas)
    }

    @Test
    fun `empty values produce an empty safe state`() {
        repository.emitIdeas(emptyMap())
        repository.emitValues(emptyList())

        val state = requireNotNull(viewModel.state.value)
        assertNull(state.selectedValueId)
        assertTrue(state.ideas.isEmpty())
        assertFalse(state.isLoading)
    }

    @Test
    fun `blank idea is rejected without writing to Firebase`() {
        repository.emitValues(listOf(ValueOption(id = "1", name = "Health")))

        val accepted = viewModel.addIdea("   ")

        assertFalse(accepted)
        assertTrue(repository.addRequests.isEmpty())
        assertEquals("Idea cannot be blank", viewModel.state.value?.errorMessage)
    }

    @Test
    fun `unchanged edit does not write to Firebase`() {
        val idea = Idea(id = "idea-1", value = "Walk")
        repository.emitValues(listOf(ValueOption(id = "1", name = "Health")))

        val accepted = viewModel.editIdea(idea, " Walk ")

        assertTrue(accepted)
        assertTrue(repository.editRequests.isEmpty())
    }

    @Test
    fun `write failure is exposed as readable UI state`() {
        repository.nextOperationResult = Result.failure(IllegalStateException("Permission denied"))
        repository.emitValues(listOf(ValueOption(id = "1", name = "Health")))

        viewModel.addIdea("Walk")

        assertEquals("Permission denied", viewModel.state.value?.errorMessage)
    }

    @Test
    fun `delete uses the currently selected value`() {
        val idea = Idea(id = "idea-7", value = "Stretch")
        repository.emitValues(
            listOf(
                ValueOption(id = "1", name = "Health"),
                ValueOption(id = "2", name = "Learning"),
            ),
        )
        viewModel.selectValue("2")

        viewModel.deleteIdea(idea)

        assertEquals(listOf(DeleteRequest("2", "idea-7")), repository.deleteRequests)
    }

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
            value: String,
            onComplete: IdeasRepository.OperationCallback,
        ) {
            addRequests += AddRequest(valueId, value)
            onComplete.onComplete(nextOperationResult)
        }

        override fun editIdea(
            valueId: String,
            ideaId: String,
            value: String,
            onComplete: IdeasRepository.OperationCallback,
        ) {
            editRequests += EditRequest(valueId, ideaId, value)
            onComplete.onComplete(nextOperationResult)
        }

        override fun deleteIdea(
            valueId: String,
            ideaId: String,
            onComplete: IdeasRepository.OperationCallback,
        ) {
            deleteRequests += DeleteRequest(valueId, ideaId)
            onComplete.onComplete(nextOperationResult)
        }

        fun emitValues(values: List<ValueOption>) = observer.onValuesChanged(values)

        fun emitIdeas(ideasByValue: Map<String, List<Idea>>) = observer.onIdeasChanged(ideasByValue)
    }

    private data class AddRequest(val valueId: String, val value: String)
    private data class EditRequest(val valueId: String, val ideaId: String, val value: String)
    private data class DeleteRequest(val valueId: String, val ideaId: String)
}
