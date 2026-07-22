package org.kaleta.objectives.ui

import android.graphics.Rect
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.LinearLayout
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsAnimationCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updateLayoutParams
import androidx.core.view.updatePadding
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputLayout
import com.google.android.material.textfield.TextInputEditText
import org.kaleta.objectives.R
import org.kaleta.objectives.adapter.IdeasAdapter
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.SubvalueOption
import org.kaleta.objectives.data.ValueOption
import org.kaleta.objectives.repository.AppRepositoryProvider
import kotlin.math.max

class MainFragment : Fragment() {
    private lateinit var viewModel: MainViewModel
    private var edgeRollEffect: EdgeRollEffect? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        viewModel = ViewModelProvider(
            this,
            MainViewModelFactory(AppRepositoryProvider.create(requireContext().applicationContext)),
        )[MainViewModel::class.java]
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?,
    ): View = inflater.inflate(R.layout.fragment_main, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val valueSpinner: Spinner = view.findViewById(R.id.valueSpinner)
        val valueSpinnerFrame: View = view.findViewById(R.id.valueSpinnerFrame)
        val subvalueSpinner: Spinner = view.findViewById(R.id.subvalueSpinner)
        val recyclerView: RecyclerView = view.findViewById(R.id.ideas)
        val addButton: MaterialButton = view.findViewById(R.id.addIdea)
        val topAppBar: MaterialToolbar = view.findViewById(R.id.topAppBar)
        val displayedValues = mutableListOf<ValueOption>()
        val displayedSubvalues = mutableListOf<SubvalueOption>()
        val valuesAdapter = ArrayAdapter(
            requireContext(),
            R.layout.spinner_selected_item,
            android.R.id.text1,
            displayedValues,
        ).apply {
            setDropDownViewResource(R.layout.spinner_dropdown_item)
            setNotifyOnChange(false)
        }
        val ideasAdapter = IdeasAdapter(
            onDeleteRequested = ::showDeleteConfirmation,
            onEditRequested = viewModel::editIdea,
        )
        var renderedValueId: String? = null
        var renderedSubvalueId: String? = null

        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = ideasAdapter
        edgeRollEffect = EdgeRollEffect(recyclerView).also { it.attach() }
        recyclerView.isClickable = true
        recyclerView.setOnClickListener { ideasAdapter.stopEditing() }
        recyclerView.setOnTouchListener { _, event ->
            if (
                event.action == MotionEvent.ACTION_UP &&
                recyclerView.findChildViewUnder(event.x, event.y) == null
            ) {
                ideasAdapter.stopEditing()
            }
            false
        }

        val buttonMargin = resources.getDimensionPixelOffset(R.dimen.dp_10)
        val focusedIdeaMargin = resources.getDimensionPixelOffset(R.dimen.dp_10)
        val revealFocusedIdea = Runnable {
            val focusedView = recyclerView.findFocus() ?: return@Runnable
            val ideaView = recyclerView.findContainingItemView(focusedView) ?: return@Runnable
            recyclerView.requestChildRectangleOnScreen(
                ideaView,
                Rect(0, 0, ideaView.width, ideaView.height + focusedIdeaMargin),
                true,
            )
        }

        fun applyWindowInsets(insets: WindowInsetsCompat) {
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            val ime = insets.getInsets(WindowInsetsCompat.Type.ime())
            val keyboardPadding = max(ime.bottom - systemBars.bottom, 0)
            topAppBar.updatePadding(top = systemBars.top)
            valueSpinnerFrame.updatePadding(bottom = systemBars.bottom)
            addButton.updateLayoutParams<ViewGroup.MarginLayoutParams> {
                bottomMargin = buttonMargin + systemBars.bottom
            }
            if (view.paddingBottom != keyboardPadding) {
                view.updatePadding(bottom = keyboardPadding)
                if (keyboardPadding > 0) {
                    recyclerView.removeCallbacks(revealFocusedIdea)
                    recyclerView.post(revealFocusedIdea)
                }
            }
        }

        ViewCompat.setOnApplyWindowInsetsListener(view) { _, insets ->
            applyWindowInsets(insets)
            insets
        }
        ViewCompat.setWindowInsetsAnimationCallback(
            view,
            object : WindowInsetsAnimationCompat.Callback(DISPATCH_MODE_CONTINUE_ON_SUBTREE) {
                override fun onProgress(
                    insets: WindowInsetsCompat,
                    runningAnimations: MutableList<WindowInsetsAnimationCompat>,
                ): WindowInsetsCompat {
                    applyWindowInsets(insets)
                    return insets
                }

                override fun onEnd(animation: WindowInsetsAnimationCompat) {
                    if (animation.typeMask and WindowInsetsCompat.Type.ime() != 0) {
                        recyclerView.removeCallbacks(revealFocusedIdea)
                        recyclerView.post(revealFocusedIdea)
                    }
                }
            },
        )
        ViewCompat.requestApplyInsets(view)

        valueSpinner.adapter = valuesAdapter
        valueSpinner.prompt = getString(R.string.select_value)
        valueSpinner.gravity = Gravity.CENTER
        valueSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
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

        val subvaluesAdapter = ArrayAdapter(
            requireContext(),
            R.layout.spinner_selected_item,
            android.R.id.text1,
            displayedSubvalues,
        ).apply {
            setDropDownViewResource(R.layout.spinner_dropdown_item)
            setNotifyOnChange(false)
        }
        subvalueSpinner.adapter = subvaluesAdapter
        subvalueSpinner.prompt = getString(R.string.select_subvalue)
        subvalueSpinner.gravity = Gravity.CENTER
        subvalueSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: AdapterView<*>?,
                selectedView: View?,
                position: Int,
                id: Long,
            ) {
                displayedSubvalues.getOrNull(position)?.let { subvalue ->
                    viewModel.selectSubvalue(subvalue.id)
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

            val selectedValuePosition = displayedValues.indexOfFirst { it.id == state.selectedValueId }
            if (selectedValuePosition >= 0 && valueSpinner.selectedItemPosition != selectedValuePosition) {
                valueSpinner.setSelection(selectedValuePosition, false)
            }

            if (displayedSubvalues != state.subvalues) {
                displayedSubvalues.clear()
                displayedSubvalues.addAll(state.subvalues)
                subvaluesAdapter.notifyDataSetChanged()
            }

            val selectedSubvaluePosition = displayedSubvalues.indexOfFirst { it.id == state.selectedSubvalueId }
            if (selectedSubvaluePosition >= 0 && subvalueSpinner.selectedItemPosition != selectedSubvaluePosition) {
                subvalueSpinner.setSelection(selectedSubvaluePosition, false)
            }

            if (
                renderedValueId != state.selectedValueId ||
                renderedSubvalueId != state.selectedSubvalueId
            ) {
                ideasAdapter.stopEditing()
                renderedValueId = state.selectedValueId
                renderedSubvalueId = state.selectedSubvalueId
            }
            ideasAdapter.submitList(state.ideas)
            addButton.isEnabled = state.selectedValueId != null && state.selectedSubvalueId != null

            state.errorMessage?.let { message ->
                Toast.makeText(requireContext(), message, Toast.LENGTH_LONG).show()
                viewModel.clearError()
            }
        }
    }

    override fun onDestroyView() {
        edgeRollEffect?.detach()
        edgeRollEffect = null
        super.onDestroyView()
    }

    private fun showAddIdeaDialog() {
        val state = viewModel.state.value ?: return
        val selectedValue = state.selectedValue ?: return
        val selectedSubvalue = state.selectedSubvalue ?: return
        val dialogContent = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(
                resources.getDimensionPixelOffset(R.dimen.dp_19),
                0,
                resources.getDimensionPixelOffset(R.dimen.dp_19),
                0,
            )
        }
        val nameInputLayout = TextInputLayout(requireContext()).apply {
            boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
            hint = getString(R.string.name)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
            ).apply {
                bottomMargin = resources.getDimensionPixelOffset(R.dimen.dp_5)
            }
        }
        val nameInput = TextInputEditText(requireContext()).apply {
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE or
                    InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            minLines = 1
            maxLines = 5
            gravity = Gravity.TOP
        }
        nameInputLayout.addView(nameInput)
        val descriptionInputLayout = TextInputLayout(requireContext()).apply {
            boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
            hint = getString(R.string.description)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
            )
        }
        val descriptionInput = TextInputEditText(requireContext()).apply {
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE or
                InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            minLines = 1
            maxLines = 5
            gravity = Gravity.TOP
        }
        descriptionInputLayout.addView(descriptionInput)
        dialogContent.addView(nameInputLayout)
        dialogContent.addView(descriptionInputLayout)

        val dialog = MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.new_idea)
            .setMessage("${selectedValue.name} / ${selectedSubvalue.displayName}")
            .setView(dialogContent)
            .setPositiveButton(R.string.add, null)
            .setNegativeButton(R.string.cancel, null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                if (viewModel.addIdea(nameInput.text.toString(), descriptionInput.text.toString())) {
                    dialog.dismiss()
                } else {
                    nameInputLayout.error = getString(R.string.idea_required)
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
