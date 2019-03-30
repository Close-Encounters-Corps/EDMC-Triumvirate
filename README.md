﻿# EDMC-Triumvirate
Плагин для EDMC, который автоматически собирает научную информацию и позволяет координировать миссии
EDMC plugin to automatically collect accurate science data from the galaxy and coordinate missions

# Важно!!!

Этот плагин не совместим с EDMC-USS-Survey, с EDMC-USS-Survey-Triumvirate-edition и с EDMC-Canonn. С первыми двумя просто потому что они устарели, а третий просто интегрирован в этот =)
The USS Survey and EDMC-Canonn are no longer compatible. However EDMC-Canonn now writes to the same google sheets as the USS-Survey so if you are using this plugin, then please disable the USS-Survey

# Функции
  
## Координационая система

Система координирования может быть использована для направления людей на точки интереса. В систему входит:
The Patrol system will eventualy be used for directing people to places of interest to Canonn. This will be based on the legacy patrol system for now. In addition we now have two extra patrol types. 
 
 * Система слежения за Влиянием в системах: Этот инструмент дает краткую сводку по состоянию систем с нашими фракциями 
 * Canonn Influence Patrol: This tells you where systems have a Canonn Presence and gives some informatio about the current state
 * Расположение кораблей: Инструмент, показывающий где находятся ваши корабли
 * Ship Locations: This tells you where your ships are located
 

## Новостной узел
Читайте последние новости
See the top stories on rotation

## Отчеты об таргоидских перехватах
Позволяет собирать информацию об таргоидских перехватах.
Hyperdiction reporting is logged from the Thargoid Encounter Stats screen. There is also a button in the settings which will allow you to upload all hyperdictions from your journal. 

## Отчеты об NHSS
Собирает информацию об обнаруженых Таргоидских сигналах.
This captures NHSS information from the FSS scanner and USS Drops. Only logs one instance of each threat level per system

## Кодекс
Собирает информацию об записях журнала
This records the codex entries and a bit of extra info about body and lat lon. The codex entries are routed to the appropriate CAPI report. eg fgreports btreports etc.

## Убийства таргоидов
Записывает информацию об сбитых таргоидах
This records Thargoids kills. What else did you expect herds of wilderbeast running through the serengeti?

## Информация из журнала
Отправляет информацию из журнала нам, кроме той информации, которая нам не нужна.
This records all journal entries that haven't specifically been excluded. NB the exclusion list needs to be bigger.

## FSS репортер
Отправляет информацию об сигналах в системе
This records FSSSignalDicovered Messages that havent beenexcluded. Also records AX Conflict Zones in their own model

