package org.kaleta.objectives.ui

import android.os.Bundle
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updateLayoutParams
import androidx.core.view.updatePadding
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.textfield.TextInputLayout
import org.kaleta.objectives.R
import org.kaleta.objectives.adapter.IdeasAdapter
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.ValueOption
import org.kaleta.objectives.repository.LegacyFirebaseIdeasRepository

class MainFragment : Fragment() {
    private lateinit var viewModel: MainViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        viewModel = ViewModelProvider(
            this,
            MainViewModelFactory(LegacyFirebaseIdeasRepository()),
        )[MainViewModel::class.java]
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?,
    ): View = inflater.inflate(R.layout.fragment_main, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val spinner: Spinner = view.findViewById(R.id.valueSpinner)
        val recyclerView: RecyclerView = view.findViewById(R.id.ideas)
        val addButton: FloatingActionButton = view.findViewById(R.id.addIdea)
        val topAppBar: MaterialToolbar = view.findViewById(R.id.topAppBar)
        val displayedValues = mutableListOf<ValueOption>()
        val valuesAdapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_item,
            displayedValues,
        ).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            setNotifyOnChange(false)
        }
        val ideasAdapter = IdeasAdapter(
            onDeleteRequested = ::showDeleteConfirmation,
            onEditRequested = viewModel::editIdea,
        )
        var renderedValueId: String? = null

        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = ideasAdapter

        val fabMargin = resources.getDimensionPixelOffset(R.dimen.fab_margin)
        val listBottomPadding = resources.getDimensionPixelOffset(R.dimen.idea_list_bottom_padding)
        ViewCompat.setOnApplyWindowInsetsListener(view) { _, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            topAppBar.updatePadding(top = systemBars.top)
            recyclerView.updatePadding(bottom = listBottomPadding + systemBars.bottom)
            addButton.updateLayoutParams<ViewGroup.MarginLayoutParams> {
                bottomMargin = fabMargin + systemBars.bottom
            }
            insets
        }
        ViewCompat.requestApplyInsets(view)

        spinner.adapter = valuesAdapter
        spinner.prompt = getString(R.string.select_value)
        spinner.gravity = Gravity.CENTER
        spinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: AdapterView<*>?,
                selectedView: View?,
                position: Int,
                id: Long,
            ) {
                displayedValues.getOrNull(position)?.let { value ->
                    viewModel.selectValue(value.id)
                }
            }

            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }

        addButton.setOnClickListener { showAddIdeaDialog() }

        viewModel.state.observe(viewLifecycleOwner) { state ->
            if (displayedValues != state.values) {
                displayedValues.clear()
                displayedValues.addAll(state.values)
                valuesAdapter.notifyDataSetChanged()
            }

            val selectedPosition = displayedValues.indexOfFirst { it.id == state.selectedValueId }
            if (selectedPosition >= 0 && spinner.selectedItemPosition != selectedPosition) {
                spinner.setSelection(selectedPosition, false)
            }

            if (renderedValueId != state.selectedValueId) {
                ideasAdapter.stopEditing()
                renderedValueId = state.selectedValueId
            }
            ideasAdapter.submitList(state.ideas)
            addButton.isEnabled = state.selectedValueId != null

            state.errorMessage?.let { message ->
                Toast.makeText(requireContext(), message, Toast.LENGTH_LONG).show()
                viewModel.clearError()
            }
        }
    }

    private fun showAddIdeaDialog() {
        val state = viewModel.state.value ?: return
        val selectedValue = state.selectedValue ?: return
        val inputLayout = TextInputLayout(requireContext()).apply {
            setPadding(
                resources.getDimensionPixelOffset(R.dimen.dp_19),
                0,
                resources.getDimensionPixelOffset(R.dimen.dp_19),
                0,
            )
        }
        val input = EditText(requireContext())
        inputLayout.addView(input)

        val dialog = MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.new_idea)
            .setMessage(selectedValue.name)
            .setView(inputLayout)
            .setPositiveButton(R.string.add, null)
            .setNegativeButton(R.string.cancel, null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                if (viewModel.addIdea(input.text.toString())) {
                    dialog.dismiss()
                } else {
                    input.error = getString(R.string.idea_required)
                }
            }
        }
        dialog.show()
    }

    private fun showDeleteConfirmation(idea: Idea) {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.delete_idea_question)
            .setPositiveButton(R.string.confirm) { dialog, _ ->
                viewModel.deleteIdea(idea)
                dialog.dismiss()
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    companion object {
        fun newInstance() = MainFragment()
    }
}
