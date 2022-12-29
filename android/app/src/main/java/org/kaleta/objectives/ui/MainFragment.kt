package org.kaleta.objectives.ui

import androidx.lifecycle.ViewModelProvider
import android.os.Bundle
import android.view.Gravity
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.floatingactionbutton.FloatingActionButton
import org.kaleta.objectives.*
import org.kaleta.objectives.adapter.IdeasAdapter
import org.kaleta.objectives.listener.AdapterValueEventListener
import org.kaleta.objectives.listener.AddIdeaOnClickListener

class MainFragment : Fragment(), AdapterView.OnItemSelectedListener, ValueParameter{

    companion object {
        fun newInstance() = MainFragment()
    }

    private var valueId: String = "1"

    private lateinit var viewModel: MainViewModel

    private val ideasAdapter = IdeasAdapter(this)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        viewModel = ViewModelProvider(this).get(MainViewModel::class.java)
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        val root = inflater.inflate(R.layout.fragment_main, container, false)

        val spinner: Spinner = root.findViewById(R.id.valueSpinner)

        var labelsAdapter = ArrayAdapter(root.context, android.R.layout.simple_spinner_item, DataSource.labels)
        labelsAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        DataSource.labelsReference.addValueEventListener(AdapterValueEventListener(labelsAdapter))

        with(spinner)
        {
            adapter = labelsAdapter
            setSelection(0, false)
            onItemSelectedListener = this@MainFragment
            prompt = "Select Value"
            gravity = Gravity.CENTER

        }

        val recyclerView: RecyclerView = root.findViewById(R.id.ideas)

        viewModel.text.observe(viewLifecycleOwner, Observer {

            recyclerView.layoutManager = LinearLayoutManager(root.context)
            recyclerView.adapter = ideasAdapter
        })

        val fab: FloatingActionButton = root.findViewById(R.id.addIdea)
        fab.setOnClickListener(AddIdeaOnClickListener(fab.context, this))

        return root
    }

    override fun setValueId(valueId: String) {
        this.valueId = valueId
    }

    override fun getValueId(): String {
        return this.valueId
    }

    override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
        this.setValueId(DataSource.labelIds.get(position))
        ideasAdapter.notifyDataSetChanged()
    }

    override fun onNothingSelected(p0: AdapterView<*>?) {

    }
}