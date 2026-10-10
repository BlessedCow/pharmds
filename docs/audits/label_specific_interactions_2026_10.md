# Label-specific interaction follow-up

These nine rules add policy and context that the existing enzyme and transporter
roles alone do not convey. The named pair must be selected for the rule to fire.
The links below are the product labels referenced directly by the rule files.

| Pair | Label source | Rule interpretation |
| --- | --- | --- |
| Theophylline + tobacco smoke | [Theophylline solution, Smokers](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=32b9780f-c46f-4e0f-9641-2cab60600e6e) | Ongoing smoking increases clearance. After cessation, clearance can fall; check concentrations. The label says nicotine gum does not reproduce the smoke effect. |
| Clozapine + tobacco smoke | [Clozapine tablets, Drug Interactions](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=25c0c6d5-f7b0-48e4-e054-00144ff8d46c) | Smoke induces CYP1A2; discontinuing smoking can raise clozapine exposure. |
| Simvastatin + grapefruit juice | [Simvastatin tablets, Drug Interactions](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=7fce939e-c38e-497f-ba3f-e7b6ba44bfd9) | Label warns against large amounts, more than one quart daily. The effect depends on quantity and preparation. |
| Apixaban + St. John's wort or phenytoin | [Eliquis, Drug Interactions 7.2](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=7be1f4c1-bb2f-4ded-ae9a-515d2a22f93e) | Both are explicitly named among combined P-gp and strong CYP3A4 inducers to avoid. |
| Rivaroxaban + St. John's wort or phenytoin | [Xarelto, Drug Interactions 7.3](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=38b11f5d-f0fc-46dc-aef1-ea31872bb621) | Both are explicitly named among combined P-gp and strong CYP3A4 inducers to avoid. |
| Rivaroxaban + ketoconazole or ritonavir | [Xarelto, Drug Interactions 7.2](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=38b11f5d-f0fc-46dc-aef1-ea31872bb621) | Both are explicitly named combined P-gp and strong CYP3A4 inhibitors to avoid. |

The current input records the presence of `tobacco_smoke`, not when smoking
started or stopped. The rules describe both directions conditionally and do not
calculate a dose adjustment. A selected grapefruit juice entry does not record
the amount consumed, so the simvastatin rule asks for it instead of assuming
that the high-volume warning applies.

Apixaban has dose-dependent instructions for combined strong CYP3A4/P-gp
inhibitors. A selected product strength is not the administered dose, so this
batch does not turn ketoconazole or ritonavir with apixaban into an unqualified
avoid rule. Likewise, the pair-specific phenytoin warnings do not invent a
general P-gp transporter assignment for phenytoin.

For the named avoid pairs, the legacy generic CYP3A4 rule's weaker monitoring
advice is suppressed in the rule output. Other CYP3A4 pairs still use that rule.
