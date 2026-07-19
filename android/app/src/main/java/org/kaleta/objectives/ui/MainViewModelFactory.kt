package org.kaleta.objectives.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import org.kaleta.objectives.repository.IdeasRepository

class MainViewModelFactory(
    private val repository: IdeasRepository,
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        require(modelClass.isAssignableFrom(MainViewModel::class.java)) {
            "Unknown ViewModel class: ${modelClass.name}"
        }

        @Suppress("UNCHECKED_CAST")
        return MainViewModel(repository) as T
    }
}
