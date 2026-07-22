package org.kaleta.objectives.repository

import android.content.Context
import org.json.JSONObject
import org.kaleta.objectives.data.Idea
import org.kaleta.objectives.data.IdeasData
import org.kaleta.objectives.data.SubvalueOption
import org.kaleta.objectives.data.ValueOption

object DevIdeasDataLoader {
    fun load(context: Context): IdeasData {
        val json = context.assets.open(ASSET_NAME).bufferedReader().use { reader ->
            JSONObject(reader.readText())
        }
        val valuesJson = json.getJSONObject(VALUES_FIELD)
        val values = mutableListOf<ValueOption>()
        val subvaluesByValue = mutableMapOf<String, List<SubvalueOption>>()
        val ideasByValueAndSubvalue = mutableMapOf<String, Map<String, List<Idea>>>()

        valuesJson.keys().asSequence().sorted().forEach { valueId ->
            val valueJson = valuesJson.getJSONObject(valueId)
            values += ValueOption(valueId, valueJson.getString(NAME_FIELD))
            val subvaluesJson = valueJson.getJSONObject(SUBVALUES_FIELD)
            val subvalues = mutableListOf<SubvalueOption>()
            val ideasBySubvalue = mutableMapOf<String, List<Idea>>()

            subvaluesJson.keys().asSequence().sorted().forEach { subvalueId ->
                val subvalueJson = subvaluesJson.getJSONObject(subvalueId)
                subvalues += SubvalueOption(subvalueId, subvalueJson.getString(NAME_FIELD))
                val ideasJson = subvalueJson.getJSONObject(IDEAS_FIELD)
                ideasBySubvalue[subvalueId] = ideasJson.keys().asSequence().sorted().map { ideaId ->
                    val ideaJson = ideasJson.getJSONObject(ideaId)
                    Idea(
                        id = ideaId,
                        name = ideaJson.getString(NAME_FIELD),
                        description = ideaJson.optString(DESCRIPTION_FIELD),
                    )
                }.toList()
            }

            subvaluesByValue[valueId] = subvalues
            ideasByValueAndSubvalue[valueId] = ideasBySubvalue
        }

        return IdeasData(values, subvaluesByValue, ideasByValueAndSubvalue)
    }

    private const val ASSET_NAME = "ideas-data.json"
    private const val VALUES_FIELD = "values"
    private const val SUBVALUES_FIELD = "subvalues"
    private const val IDEAS_FIELD = "ideas"
    private const val NAME_FIELD = "name"
    private const val DESCRIPTION_FIELD = "description"
}
