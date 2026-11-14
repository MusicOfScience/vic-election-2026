# How often did leading independents reach the final two?

Run `python model/scripts/audit_independent_final_pair.py` from the repository
root. The audit takes the highest-polling independent in each district with
an independent, ranks them across all candidates by actual first preferences,
then checks their name against the Victorian Electoral Commission final pair.
It covers 2014, 2018 and 2022 general elections. Early-majority seats without a
documented pair are unknown. The Narracan supplementary election is excluded.

| First-preference rank | In documented final pair | Out of documented final pair | Unknown |
| --- | ---: | ---: | ---: |
| First | 2 | 0 | 0 |
| Second | 10 | 0 | 1 |
| Third | 1 | 19 | 1 |
| Fourth or lower | 0 | 116 | 30 |

The sole third-place survivor was in 2018. These are observed conditional
counts for all leading independents, not a teal-specific or forecast
probability. Rank is measured after the votes were cast, and the small
upper-rank samples and nonrandom missing counts limit generalisation.

For the next model, evaluate first-preference rank uncertainty before assigning
a final-two likelihood. Track the named candidate's gap to the second-ranked
candidate and preference sources still in the count. A shared campaign shock
can move several candidates closer to second; it supplies no evidence that
they will each overtake the particular opponent in their electorate.
