Generell wird empfohlen, diese Container nur in einer Linux Umgebung auszuführen.
Bei Windows kann es passieren, dass die Container nicht richtig starten!

In der .env Datei muss die REACT_APP_API_URL genauso wie im Frontend gesetzt sein!
Bei den SMTP Ports müssen alle Daten ausgefüllt werden.
TOKEN_EXPIRY_MINUTES gibt an, wie lange ein Token während einer Session maximal gültig ist.
AUTH_CODE_EXPIRY_MINUTES gibt an, wie lange ein Authentifizierungscode während des Registrier- und Passwordzurücksetzprozess gültig ist.
Der SECRET-KEY gibt den Bypass zum Token für den Cronjob an, bitte modifzieren!

Auf der Ebene von dem app-Ordner folgende Befehle ausführen:
```sh
$ docker compose build
```

und danach:
```sh
docker compose up
```
Standardmäßig sind die API unter folgender Adresse zu finden: [http://fastapi.localhost:8008/docs](http://fastapi.localhost:8008/docs).

Um die Test durchzuführen, muss zuerst folgendes asugeführt werden:
docker compose down 
Danach folgender Befehl:
```sh
docker compose -f docker-compose_test.yml build
docker compose -f docker-compose_test.yml up
```
In einem anderem Tab kann folgender Befehl dann ausgeführt werden.
```sh
docker compose exec web pytest
```
Die Tests können nur einmal gestartet werden, beim zweiten Durchlauf schlagen sie automatisch fehl.
Um sie neu durchzuführen, muss Folgendes ausgeführt werden:
```sh
docker compose -f docker-compose_test.yml down
docker compose -f docker-compose_test.yml up
```
Und schließlich können die Tests neu durchgeführt werden.

Als Basis diente: [https://github.com/ed-roh/react-admin-dashboard](https://github.com/ed-roh/react-admin-dashboard)
