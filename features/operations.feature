Feature: Operations

    Scenario Outline: Test Setup
        Given the <sample> sample image
        Then the image should match the <reference> reference image

        Examples:
            | sample    | reference         |
            | chelsea   | chelsea           |

    Scenario Outline: solid
        Given an empty graph
       And a task <task> with operator solid layer <layer> size <size> values <values> components <components> role <role>
        When retrieving the output image from task <task>
        Then the image should match the <reference> reference image

        Examples:
            | task       | layer  | size        | values          | components       | role              | reference           |
            | "/solid"   | "C"    | (128, 128)  | (1, 0.5, 0)    | ["r", "g", "b"]  | imagecat.Role.RGB | solid-color         |

