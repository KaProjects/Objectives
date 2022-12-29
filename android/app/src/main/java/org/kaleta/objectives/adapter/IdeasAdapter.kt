package org.kaleta.objectives.adapter

import android.app.AlertDialog
import android.graphics.PorterDuff
import android.text.Editable
import android.text.SpannableStringBuilder
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.ViewGroup.MarginLayoutParams
import androidx.recyclerview.widget.RecyclerView
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.ValueEventListener
import org.kaleta.objectives.DataSource
import org.kaleta.objectives.R
import org.kaleta.objectives.ValueParameter
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.listener.OnSwipeTouchListener
import android.view.View.OnLongClickListener
import android.widget.*
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout


class IdeasAdapter(valueParameter: ValueParameter): RecyclerView.Adapter<IdeasAdapter.ViewHolder>(), ValueEventListener {

    val valueParameter: ValueParameter

    private val views = ArrayList<ViewHolder>()

    init{
        DataSource.ideasReference.addValueEventListener(this)
        this.valueParameter = valueParameter
    }

    fun resetViews(){
        for (view in views){
            view.hideButtons()
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = ViewHolder(
            LayoutInflater.from(parent.context)
                .inflate(R.layout.idea_item, parent, false),
            this)
        views.add(view)
        return view
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        var ideasList = DataSource.ideasMap.get(valueParameter.getValueId())!!
        holder.bind(ideasList.get(position))
    }

    override fun getItemCount(): Int {
        if (DataSource.ideasMap.keys.size == 0)
            return 0
        var ideasList = DataSource.ideasMap.get(valueParameter.getValueId())
        return ideasList?.size ?: 0
    }


    class ViewHolder(itemView: View, val adapter: IdeasAdapter) : RecyclerView.ViewHolder(itemView) {

        var ideaView: TextView = itemView.findViewById(R.id.idea)
        var ideaEdit: TextInputEditText = itemView.findViewById(R.id.ideaEdit)
        var deleteButton: ImageView = itemView.findViewById(R.id.deleteIdea)
        var confirmEditButton: ImageView = itemView.findViewById(R.id.confirmEditIdea)


        fun bind(idea: Idea) {
            ideaView.text = idea.value
            ideaEdit.text = SpannableStringBuilder(idea.value)

            deleteButton.visibility = View.INVISIBLE
            ideaEdit.visibility = View.INVISIBLE
            confirmEditButton.visibility = View.INVISIBLE

            itemView.setOnClickListener {
                adapter.resetViews()
                true
            }
            itemView.setOnLongClickListener {
                adapter.resetViews()
                deleteButton.visibility = View.VISIBLE
                confirmEditButton.visibility = View.VISIBLE
                ideaEdit.text = SpannableStringBuilder(idea.value)
                ideaEdit.visibility = View.VISIBLE
                ideaView.visibility = View.INVISIBLE
                true
            }
            deleteButton.setOnTouchListener { v, event ->
                when (event.action) {
                    MotionEvent.ACTION_UP -> {
                        val alert = AlertDialog.Builder(itemView.context)
                            .setTitle("Delete Idea?")
                            .setPositiveButton("Confirm") { dialog, _ ->
                                DataSource.deleteIdea(adapter.valueParameter.getValueId(), idea.id)
                                dialog.cancel()
                                adapter.resetViews()
                            }
                            .setNegativeButton("Cancel") { dialog, _ ->
                                dialog.cancel()
                            }.create()

                        alert.show()
                    }
                }
                false
            }
            confirmEditButton.setOnTouchListener { v, event ->
                when (event.action) {
                    MotionEvent.ACTION_UP -> {
                        DataSource.editIdea(adapter.valueParameter.getValueId(), idea.id, ideaEdit.text.toString())
                        adapter.resetViews()
                    }
                }
                false
            }
        }

        fun hideButtons(){
            deleteButton.visibility = View.INVISIBLE
            confirmEditButton.visibility = View.INVISIBLE
            ideaEdit.visibility = View.INVISIBLE
            ideaView.visibility = View.VISIBLE
        }
    }

    override fun onCancelled(p0: DatabaseError) {
        println(p0.message)
    }

    override fun onDataChange(p0: DataSnapshot) {
//        views.clear()
        this.notifyDataSetChanged();
    }
}
