package org.kaleta.objectives.adapter

import android.text.SpannableStringBuilder
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.textfield.TextInputEditText
import org.kaleta.objectives.R
import org.kaleta.objectives.data.Idea

class IdeasAdapter(
    private val onDeleteRequested: (Idea) -> Unit,
    private val onEditRequested: (Idea, String) -> Boolean,
) : ListAdapter<Idea, IdeasAdapter.ViewHolder>(IdeaDiffCallback) {
    private var editingIdeaId: String? = null

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.idea_item, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val idea = getItem(position)
        holder.bind(idea, isEditing = idea.id == editingIdeaId)
    }

    fun stopEditing() {
        updateEditingIdea(null)
    }

    private fun updateEditingIdea(ideaId: String?) {
        if (editingIdeaId == ideaId) return

        val previousId = editingIdeaId
        editingIdeaId = ideaId
        notifyIdeaChanged(previousId)
        notifyIdeaChanged(ideaId)
    }

    private fun notifyIdeaChanged(ideaId: String?) {
        val position = currentList.indexOfFirst { it.id == ideaId }
        if (position >= 0) notifyItemChanged(position)
    }

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val ideaView: TextView = itemView.findViewById(R.id.idea)
        private val ideaEdit: TextInputEditText = itemView.findViewById(R.id.ideaEdit)
        private val deleteButton: ImageView = itemView.findViewById(R.id.deleteIdea)
        private val confirmEditButton: ImageView = itemView.findViewById(R.id.confirmEditIdea)

        fun bind(idea: Idea, isEditing: Boolean) {
            ideaView.text = idea.value
            ideaEdit.text = SpannableStringBuilder(idea.value)
            showEditingState(isEditing)

            itemView.setOnClickListener { stopEditing() }
            itemView.setOnLongClickListener {
                updateEditingIdea(idea.id)
                true
            }
            deleteButton.setOnClickListener {
                onDeleteRequested(idea)
            }
            confirmEditButton.setOnClickListener {
                if (onEditRequested(idea, ideaEdit.text?.toString().orEmpty())) {
                    stopEditing()
                } else {
                    ideaEdit.error = itemView.context.getString(R.string.idea_required)
                }
            }
        }

        private fun showEditingState(isEditing: Boolean) {
            val editVisibility = if (isEditing) View.VISIBLE else View.INVISIBLE
            deleteButton.visibility = editVisibility
            confirmEditButton.visibility = editVisibility
            ideaEdit.visibility = editVisibility
            ideaView.visibility = if (isEditing) View.INVISIBLE else View.VISIBLE
        }
    }

    private object IdeaDiffCallback : DiffUtil.ItemCallback<Idea>() {
        override fun areItemsTheSame(oldItem: Idea, newItem: Idea): Boolean = oldItem.id == newItem.id

        override fun areContentsTheSame(oldItem: Idea, newItem: Idea): Boolean = oldItem == newItem
    }
}
