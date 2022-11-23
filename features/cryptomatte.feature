Feature: Cryptomatte

    Scenario Outline: Matte Extraction
        Given an empty graph
        And a task "/sample" which outputs the <sample> sample image
        And a task "/cryptomatte" with operator cryptomatte clown False mattes <mattes>
        And links [("/sample", ("/cryptomatte", "image"))]
        When retrieving the output image from task "/cryptomatte"
        Then the image should match the <reference> reference image

        Examples:
            | sample                | mattes                                  | reference                   |
            | bunny-crypto-material | ["bunny_porcelain_mat"]                 | cryptomatte-bunny-porcelain |
            | bunny-crypto-material | ["flowerA_petal", "flowerB_petal"]      | cryptomatte-bunny-flowers   |


    Scenario Outline: Clown Matte Extraction
        Given an empty graph
        And a task "/sample" which outputs the <sample> sample image
        And a task "/cryptomatte" with operator cryptomatte clown True mattes <mattes>
        And links [("/sample", ("/cryptomatte", "image"))]
        When retrieving the output image from task "/cryptomatte"
        Then the image should match the <reference> reference image

        Examples:
            | sample                | mattes                                  | reference                         |
            | bunny-crypto-material | ["bunny_porcelain_mat"]                 | cryptomatte-bunny-porcelain-clown |
            | bunny-crypto-material | ["flowerA_petal", "flowerB_petal"]      | cryptomatte-bunny-flowers-clown   |
            | bunny-crypto-material | ["bunny_porcelain_mat","flowerA_petal","flowerB_petal","flowerStem_mat","grass_mat","ground_mat","smallLeaf_mat","smallStalk_mat"] | cryptomatte-bunny-all-clown |

