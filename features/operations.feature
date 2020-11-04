Feature: Operations

    Scenario Outline: Test Setup
        Given an empty graph
        And a task <task> which outputs the <sample> sample image
        When retrieving the output image from task <task>
        Then the image should match the <reference> reference image

        Examples:
            | task      | sample    | reference         |
            | "/sample" | chelsea   | chelsea           |


    Scenario Outline: solid
        Given an empty graph
        And a task <task> with operator solid layer <layer> size <size> values <values> components <components> role <role>
        When retrieving the output image from task <task>
        Then the image should match the <reference> reference image

        Examples:
            | task       | layer  | size        | values          | components       | role               | reference           |
            | "/solid"   | "C"    | (128, 128)  | (1, 0.5, 0)     | ["r", "g", "b"]  | imagecat.Role.RGB  | solid-color         |
            | "/solid"   | "vel"  | (128, 128)  | (0.0, 0.5, 1.0) | ["x", "y", "z"]  | imagecat.Role.NONE | solid-vel           |


    Scenario Outline: text
        Given an empty graph
        And a task <task> with operator text anchor <anchor> fontindex <fontindex> fontname <fontname> fontsize <fontsize> layer <layer> position <position> size <size> text <text>
        When retrieving the output image from task <task>
        Then the image should match the <reference> reference image

        Examples:
            | task    | anchor | fontindex | fontname    | fontsize | layer | position           | size       | text        | reference            |
            | "/text" | "mm"   | 0         | "Helvetica" | "0.33vh" | "A"   | ("0.5vw", "0.5vh") | (256, 128) | "Imagecat!" | text                 |
            | "/text" | "lm"   | 0         | "Helvetica" | "0.33vh" | "A"   | ("0.0vw", "0.5vh") | (256, 128) | "Imagecat!" | text-left-align      |
            | "/text" | "rm"   | 0         | "Helvetica" | "0.33vh" | "A"   | ("1.0vw", "0.5vh") | (256, 128) | "Imagecat!" | text-right-align     |

