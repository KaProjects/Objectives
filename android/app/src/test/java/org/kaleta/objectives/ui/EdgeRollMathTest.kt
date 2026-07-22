package org.kaleta.objectives.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class EdgeRollMathTest {
    @Test
    fun `fully visible row is not rolled`() {
        assertNull(EdgeRollMath.calculate(10, 110, 0, 200))
    }

    @Test
    fun `half hidden top row folds down from its bottom edge`() {
        val roll = EdgeRollMath.calculate(-50, 50, 0, 200)

        assertEquals(RollEdge.TOP, roll?.edge)
        assertEquals(34f, roll?.angle ?: 0f, 0.001f)
    }

    @Test
    fun `half hidden bottom row folds up from its top edge`() {
        val roll = EdgeRollMath.calculate(150, 250, 0, 200)

        assertEquals(RollEdge.BOTTOM, roll?.edge)
        assertEquals(-34f, roll?.angle ?: 0f, 0.001f)
    }

    @Test
    fun `row outside viewport is not rolled`() {
        assertNull(EdgeRollMath.calculate(210, 310, 0, 200))
    }

    @Test
    fun `rows exactly touching viewport edges are not rolled`() {
        assertNull(EdgeRollMath.calculate(0, 100, 0, 200))
        assertNull(EdgeRollMath.calculate(100, 200, 0, 200))
    }

    @Test
    fun `invalid zero-height row is ignored`() {
        assertNull(EdgeRollMath.calculate(20, 20, 0, 200))
    }
}
