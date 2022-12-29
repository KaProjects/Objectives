package org.kaleta.objectives.listener

import android.app.AlertDialog
import android.content.Context
import android.view.View
import android.widget.EditText
import com.google.android.material.textfield.TextInputLayout
import org.kaleta.objectives.DataSource
import org.kaleta.objectives.R
import org.kaleta.objectives.ValueParameter

class AddIdeaOnClickListener(context: Context, valueParameter: ValueParameter) : View.OnClickListener {
    private var context: Context
    private var valueParameter: ValueParameter

    init {
        this.context = context
        this.valueParameter = valueParameter
    }
    override fun onClick(p0: View?) {
        val textInputLayout = TextInputLayout(context)
        textInputLayout.setPadding(
            context.resources.getDimensionPixelOffset(R.dimen.dp_19), // if you look at android alert_dialog.xml, you will see the message textview have margin 14dp and padding 5dp. This is the reason why I use 19 here
            0,
            context.resources.getDimensionPixelOffset(R.dimen.dp_19),
            0
        )
        val input = EditText(context)
        textInputLayout.addView(input)

        val alert = AlertDialog.Builder(context)
            .setTitle("New Idea")
            .setView(textInputLayout)
            .setMessage(DataSource.labels.get(DataSource.labelIds.indexOf(valueParameter.getValueId())))
            .setPositiveButton("Add") { dialog, _ ->
                DataSource.addIdea(valueParameter.getValueId(), input.text.toString())
                dialog.cancel()
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.cancel()
            }.create()

        alert.show()
    }
}