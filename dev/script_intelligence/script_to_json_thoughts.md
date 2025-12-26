# Script to JSON Conversion: Thoughts & Suggestions (v1.0)

## 1. Core Philosophy: "Deep Segmentation" (深层切片)

The primary finding from the "九九：冻灵熊" case study is that a 1:1 mapping of Scene -> Segment is insufficient for high-quality video generation. Instead, we must adopt a **"Beat-based" segmentation strategy**.

*   **Original Approach**: 1 Scene = 1 Segment (Result: 7 segments). Too dense, model loses details.
*   **New Approach**: 1 Narrative Beat = 1 Segment (Result: 20 segments). High fidelity, accurate pacing.

### Why this matters:
Video generation models (like Sora/Runway) struggle with complex, multi-stage actions in a single prompt. By breaking down a scene into its atomic beats (Start -> Action -> Reaction -> Outcome), we ensure the model focuses on one specific visual evolution at a time.

## 2. The "Director's Prompt" Structure

The `prompt_text` field is no longer just a description; it is a **structured set of instructions**.

**Format:**
`[Style Tags...]；风格：...；场景：...；镜头：[Visual Description]；SFX：[Sound]`

**Key Rules:**
1.  **Style Preservation**: Always start with the standardized Style Tags block. This ensures visual consistency across all segments.
2.  **Character Tagging**: Use `[]` to wrap character names (e.g., `[九九]`, `[冻灵熊]`). This helps the parser (and potentially the model) distinguish entities from descriptive text.
3.  **Dialogue Precision**: Keep dialogue exactly as written in the script, wrapped in `""`.
4.  **Emotion/Parentheticals**: Place emotion indicators in `()` *before* the dialogue, e.g., `(惊恐) "台词"`.
5.  **Explicit VFX/SFX**: Don't just imply sound or effects. State them explicitly (e.g., `SFX: 嘎嘣！`, `VFX: 炸裂成冰晶`).

## 3. Asset Extraction

The `asset` field acts as a metadata layer for consistency checks.

*   **Characters**: List every entity appearing in the `prompt_text`.
*   **Props**: Key items that interact with characters (e.g., "转盘", "水母图标").
*   **Scene**: Standardized slugline (e.g., "极地冰原-NIGHT").

## 4. Workflow Recommendation for Script Intelligence

When parsing a new script:

1.  **Pre-processing**: Identify scene headers.
2.  **Beat Analysis**: Within each scene, identify changes in:
    *   Active Character (who is doing the main action?)
    *   Emotional Shift (is there a realization/shock?)
    *   Visual Spectacle (VFX heavy moments need their own segment)
3.  **Drafting**: Create segments based on these beats.
4.  **Refining**: Apply the "Director's Prompt" formatting rules.

## 5. Reference Material

See `reference_schema_example.json` in this directory for a gold-standard example of this structure applied to a complex animation script.
