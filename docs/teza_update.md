- > Generarea embedding-urilor - as scoate partea backend si as pune o altundeva. as explica cum functioneaza embediing-urile mai in depth

- > Aici graful de cunostinte trebuie explicat in cap 3- Graful de cunoștințe al proiectului este structurat în jurul a două tipuri 
de noduri: \texttt{Entity} — care reprezintă entități medicale de tip boală, 
simptom, medicament sau structură anatomică, identificate printr-o formă 
canonică normalizată — și \texttt{SourceChunk} — care referențiază fragmentele 
de document sursă din care au fost extrase entitățile. Relațiile dintre noduri 
acoperă cinci tipuri semantice: \texttt{MENTIONED\_IN} leagă o entitate de 
fragmentul în care apare; \texttt{DISEASE\_HAS\_SYMPTOM} și 
\texttt{CONDITION\_CAUSES\_SYMPTOM} modelează asocieri clinice; 
\texttt{DRUG\_TREATS\_DISEASE} captează relații terapeutice; iar 
\texttt{DISEASE\_DIFFERS\_FROM\_DISEASE} codifică informații de diagnostic 
diferențial. Fiecare relație stochează un scor de încredere calculat pe baza 
tipului entității și a prezenței unor expresii trigger în textul sursă.

Popularea grafului se realizează la ingestie prin extracție deterministă bazată 
pe liste de termeni medicali și aliasuri normalizate, urmată de detectarea 
relațiilor prin expresii regulate aplicate pe textul fragmentelor. La interogare, 
sistemul extrage entitățile seed din întrebarea utilizatorului și efectuează o 
parcurgere de tip BFS în graf, recuperând lanțurile de relații relevante. 
Rezultatele grafului sunt combinate cu rezultatele regăsirii vectoriale din 
Qdrant într-un raport ponderat, producând un context hibrid transmis modelului 
lingvistic pentru generarea răspunsului.

 - > as pune zona de reasoning fix dupa orchestrator in cap 3 

-> as vrea modificata diagrama orchestratorului, nu inteleg ce e small(blocat, retries = 0) 
-> este corecta diagrama de guardrails?

-> ce inseamna BM25 la mod hibrid? se intampla acum in cod?