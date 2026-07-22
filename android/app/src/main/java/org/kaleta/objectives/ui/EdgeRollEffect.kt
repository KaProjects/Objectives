package org.kaleta.objectives.ui

import android.animation.ValueAnimator
import android.view.View
import androidx.recyclerview.widget.RecyclerView
import kotlin.math.min

internal enum class RollEdge {
    TOP,
    BOTTOM,
}

internal data class EdgeRoll(
    val angle: Float,
    val edge: RollEdge,
)

internal object EdgeRollMath {
    const val MAX_ANGLE = 68f

    fun calculate(
        itemTop: Int,
        itemBottom: Int,
        viewportTop: Int,
        viewportBottom: Int,
    ): EdgeRoll? {
        val itemHeight = itemBottom - itemTop
        if (itemHeight <= 0) return null

        if (itemTop < viewportTop && itemBottom > viewportTop) {
            val hiddenFraction = min((viewportTop - itemTop).toFloat() / itemHeight, 1f)
            return EdgeRoll(hiddenFraction * MAX_ANGLE, RollEdge.TOP)
        }

        if (itemTop < viewportBottom && itemBottom > viewportBottom) {
            val hiddenFraction = min((itemBottom - viewportBottom).toFloat() / itemHeight, 1f)
            return EdgeRoll(-hiddenFraction * MAX_ANGLE, RollEdge.BOTTOM)
        }

        return null
    }
}

/**
 * Makes partially clipped rows appear to wrap around the top and bottom of the
 * list. Rotation follows scrolling directly, matching the web implementation.
 */
internal class EdgeRollEffect(
    private val recyclerView: RecyclerView,
) : RecyclerView.OnScrollListener(), RecyclerView.OnChildAttachStateChangeListener,
    View.OnLayoutChangeListener {
    private val cameraDistance = recyclerView.resources.displayMetrics.density * 380f
    private var attachedAdapter: RecyclerView.Adapter<*>? = null
    private var updateScheduled = false
    private val updateRunnable = Runnable {
        updateScheduled = false
        updateEdgeRoll()
    }
    private val dataObserver = object : RecyclerView.AdapterDataObserver() {
        override fun onChanged() = scheduleUpdate()

        override fun onItemRangeChanged(positionStart: Int, itemCount: Int) = scheduleUpdate()

        override fun onItemRangeInserted(positionStart: Int, itemCount: Int) = scheduleUpdate()

        override fun onItemRangeRemoved(positionStart: Int, itemCount: Int) = scheduleUpdate()

        override fun onItemRangeMoved(fromPosition: Int, toPosition: Int, itemCount: Int) =
            scheduleUpdate()
    }

    fun attach() {
        if (attachedAdapter != null) return
        attachedAdapter = recyclerView.adapter?.also { it.registerAdapterDataObserver(dataObserver) }
        recyclerView.addOnScrollListener(this)
        recyclerView.addOnChildAttachStateChangeListener(this)
        recyclerView.addOnLayoutChangeListener(this)
        scheduleUpdate()
    }

    fun detach() {
        recyclerView.removeCallbacks(updateRunnable)
        updateScheduled = false
        attachedAdapter?.unregisterAdapterDataObserver(dataObserver)
        attachedAdapter = null
        recyclerView.removeOnScrollListener(this)
        recyclerView.removeOnChildAttachStateChangeListener(this)
        recyclerView.removeOnLayoutChangeListener(this)
        for (index in 0 until recyclerView.childCount) {
            recyclerView.getChildAt(index).removeOnLayoutChangeListener(this)
        }
        resetVisibleChildren()
    }

    override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
        updateEdgeRoll()
    }

    override fun onChildViewAttachedToWindow(view: View) {
        reset(view)
        view.addOnLayoutChangeListener(this)
        scheduleUpdate()
    }

    override fun onChildViewDetachedFromWindow(view: View) {
        view.removeOnLayoutChangeListener(this)
        reset(view)
    }

    override fun onLayoutChange(
        view: View,
        left: Int,
        top: Int,
        right: Int,
        bottom: Int,
        oldLeft: Int,
        oldTop: Int,
        oldRight: Int,
        oldBottom: Int,
    ) {
        scheduleUpdate()
    }

    private fun scheduleUpdate() {
        if (updateScheduled) return
        updateScheduled = true
        recyclerView.postOnAnimation(updateRunnable)
    }

    private fun updateEdgeRoll() {
        resetVisibleChildren()
        if (!ValueAnimator.areAnimatorsEnabled()) return

        val viewportTop = recyclerView.paddingTop
        val viewportBottom = recyclerView.height - recyclerView.paddingBottom
        var topRowRolled = false
        var bottomRowRolled = false

        for (index in 0 until recyclerView.childCount) {
            val child = recyclerView.getChildAt(index)
            val roll = EdgeRollMath.calculate(
                itemTop = child.top,
                itemBottom = child.bottom,
                viewportTop = viewportTop,
                viewportBottom = viewportBottom,
            ) ?: continue

            when (roll.edge) {
                RollEdge.TOP -> {
                    if (topRowRolled) continue
                    topRowRolled = true
                    child.pivotY = child.height.toFloat()
                }

                RollEdge.BOTTOM -> {
                    if (bottomRowRolled) continue
                    bottomRowRolled = true
                    child.pivotY = 0f
                }
            }
            child.pivotX = child.width / 2f
            child.cameraDistance = cameraDistance
            child.rotationX = roll.angle
        }
    }

    private fun resetVisibleChildren() {
        for (index in 0 until recyclerView.childCount) reset(recyclerView.getChildAt(index))
    }

    private fun reset(view: View) {
        view.rotationX = 0f
        view.pivotX = view.width / 2f
        view.pivotY = view.height / 2f
    }
}
