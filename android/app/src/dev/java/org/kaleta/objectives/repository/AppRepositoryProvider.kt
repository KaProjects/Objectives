package org.kaleta.objectives.repository

import android.content.Context

object AppRepositoryProvider {
    fun create(context: Context): IdeasRepository = InMemoryIdeasRepository(
        DevIdeasDataLoader.load(context),
    )
}
