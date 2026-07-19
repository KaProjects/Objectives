package org.kaleta.objectives.repository

import android.content.Context
import org.json.JSONObject
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.ValueOption

data class DevIdeasData(
    val values: List<ValueOption>,
    val ideasByValue: Map<String, List<Idea>>,
)

object DevIdeasDataLoader {
    fun load(context: Context): DevIdeasData {
        val json = context.assets.open(ASSET_NAME).bufferedReader().use { reader ->
            JSONObject(reader.readText())
        }
        val labels = json.getJSONObject("labels")
        val ideas = json.getJSONObject("ideas")

        return DevIdeasData(
            values = labels.keys().asSequence().sorted().map { valueId ->
                ValueOption(id = valueId, name = labels.getString(valueId))
            }.toList(),
            ideasByValue = ideas.keys().asSequence().associateWith { valueId ->
                val ideasForValue = ideas.getJSONObject(valueId)
                ideasForValue.keys().asSequence().sorted().map { ideaId ->
                    Idea(id = ideaId, value = ideasForValue.getString(ideaId))
                }.toList()
            },
        )
    }

    private const val ASSET_NAME = "legacy-firebase-data.json"
}
