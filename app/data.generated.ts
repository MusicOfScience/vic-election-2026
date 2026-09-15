// District enrolment refreshed from the validated VEC 4 September 2026 extract.
// Run: node scripts/refresh-dashboard-enrolment.mjs

export const districts = [
  {
    "id": "albert-park",
    "name": "Albert Park",
    "region": "Southern Metropolitan",
    "enrolment": 50488,
    "enrolmentVariance": -5.133408493047718,
    "alpTpp2022": 61.150600869342895,
    "marginFromFifty": 11.150600869342895,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "ashwood",
    "name": "Ashwood",
    "region": "Southern Metropolitan",
    "enrolment": 52766,
    "enrolmentVariance": -0.8530627583615206,
    "alpTpp2022": 56.15298590919258,
    "marginFromFifty": 6.15298590919258,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "bass",
    "name": "Bass",
    "region": "Eastern Victoria",
    "enrolment": 57158,
    "enrolmentVariance": 7.3994738819992385,
    "alpTpp2022": 50.24393778378901,
    "marginFromFifty": 0.24393778378900777,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "bayswater",
    "name": "Bayswater",
    "region": "North-Eastern Metropolitan",
    "enrolment": 51197,
    "enrolmentVariance": -3.8012025554303,
    "alpTpp2022": 54.22897251109181,
    "marginFromFifty": 4.228972511091811,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "bellarine",
    "name": "Bellarine",
    "region": "Western Victoria",
    "enrolment": 59268,
    "enrolmentVariance": 11.3641488162345,
    "alpTpp2022": 58.46287616906666,
    "marginFromFifty": 8.46287616906666,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "benambra",
    "name": "Benambra",
    "region": "Northern Victoria",
    "enrolment": 51645,
    "enrolmentVariance": -2.959413754227735,
    "alpTpp2022": 36.74243345083262,
    "marginFromFifty": 13.257566549167379,
    "tppMethod": "2PP"
  },
  {
    "id": "bendigo-east",
    "name": "Bendigo East",
    "region": "Northern Victoria",
    "enrolment": 55789,
    "enrolmentVariance": 4.827132656895901,
    "alpTpp2022": 60.90915059858616,
    "marginFromFifty": 10.909150598586159,
    "tppMethod": "2CP"
  },
  {
    "id": "bendigo-west",
    "name": "Bendigo West",
    "region": "Northern Victoria",
    "enrolment": 49445,
    "enrolmentVariance": -7.093198045847421,
    "alpTpp2022": 64.34642547391897,
    "marginFromFifty": 14.34642547391897,
    "tppMethod": "2CP"
  },
  {
    "id": "bentleigh",
    "name": "Bentleigh",
    "region": "Southern Metropolitan",
    "enrolment": 54482,
    "enrolmentVariance": 2.3712889891018314,
    "alpTpp2022": 58.040780141843975,
    "marginFromFifty": 8.040780141843975,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "berwick",
    "name": "Berwick",
    "region": "South-Eastern Metropolitan",
    "enrolment": 65635,
    "enrolmentVariance": 23.327696354753844,
    "alpTpp2022": 45.28599783471671,
    "marginFromFifty": 4.71400216528329,
    "tppMethod": "2CP"
  },
  {
    "id": "box-hill",
    "name": "Box Hill",
    "region": "North-Eastern Metropolitan",
    "enrolment": 52151,
    "enrolmentVariance": -2.0086433671552,
    "alpTpp2022": 57.22562900171341,
    "marginFromFifty": 7.225629001713408,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "brighton",
    "name": "Brighton",
    "region": "Southern Metropolitan",
    "enrolment": 50457,
    "enrolmentVariance": -5.19165727170237,
    "alpTpp2022": 45.78807627323196,
    "marginFromFifty": 4.211923726768042,
    "tppMethod": "2CP"
  },
  {
    "id": "broadmeadows",
    "name": "Broadmeadows",
    "region": "Northern Metropolitan",
    "enrolment": 51190,
    "enrolmentVariance": -3.8143555054490754,
    "alpTpp2022": 65.4513938222841,
    "marginFromFifty": 15.451393822284103,
    "tppMethod": "2CP"
  },
  {
    "id": "brunswick",
    "name": "Brunswick",
    "region": "Northern Metropolitan",
    "enrolment": 55751,
    "enrolmentVariance": 4.755730928222474,
    "alpTpp2022": 84.05570261249856,
    "marginFromFifty": 34.055702612498564,
    "tppMethod": "2PP"
  },
  {
    "id": "bulleen",
    "name": "Bulleen",
    "region": "North-Eastern Metropolitan",
    "enrolment": 50852,
    "enrolmentVariance": -4.449455092070639,
    "alpTpp2022": 44.06487393391434,
    "marginFromFifty": 5.935126066085658,
    "tppMethod": "2CP"
  },
  {
    "id": "bundoora",
    "name": "Bundoora",
    "region": "North-Eastern Metropolitan",
    "enrolment": 48719,
    "enrolmentVariance": -8.457346862081922,
    "alpTpp2022": 62.735592381894634,
    "marginFromFifty": 12.735592381894634,
    "tppMethod": "2CP"
  },
  {
    "id": "carrum",
    "name": "Carrum",
    "region": "South-Eastern Metropolitan",
    "enrolment": 54182,
    "enrolmentVariance": 1.8075911311536947,
    "alpTpp2022": 59.93634099086632,
    "marginFromFifty": 9.93634099086632,
    "tppMethod": "2CP"
  },
  {
    "id": "caulfield",
    "name": "Caulfield",
    "region": "Southern Metropolitan",
    "enrolment": 50730,
    "enrolmentVariance": -4.67869222096957,
    "alpTpp2022": 47.931568468402034,
    "marginFromFifty": 2.068431531597966,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "clarinda",
    "name": "Clarinda",
    "region": "South-Eastern Metropolitan",
    "enrolment": 49302,
    "enrolmentVariance": -7.361894024802714,
    "alpTpp2022": 60.36804088251192,
    "marginFromFifty": 10.36804088251192,
    "tppMethod": "2CP"
  },
  {
    "id": "cranbourne",
    "name": "Cranbourne",
    "region": "South-Eastern Metropolitan",
    "enrolment": 57951,
    "enrolmentVariance": 8.889515219842178,
    "alpTpp2022": 58.99931693989071,
    "marginFromFifty": 8.999316939890711,
    "tppMethod": "2CP"
  },
  {
    "id": "croydon",
    "name": "Croydon",
    "region": "North-Eastern Metropolitan",
    "enrolment": 55065,
    "enrolmentVariance": 3.4667418263810577,
    "alpTpp2022": 48.62727053616425,
    "marginFromFifty": 1.3727294638357534,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "dandenong",
    "name": "Dandenong",
    "region": "South-Eastern Metropolitan",
    "enrolment": 53731,
    "enrolmentVariance": 0.9601653513716701,
    "alpTpp2022": 69.10558849501703,
    "marginFromFifty": 19.10558849501703,
    "tppMethod": "2CP"
  },
  {
    "id": "eildon",
    "name": "Eildon",
    "region": "Northern Victoria",
    "enrolment": 51387,
    "enrolmentVariance": -3.444193912063129,
    "alpTpp2022": 42.92379471228615,
    "marginFromFifty": 7.076205287713847,
    "tppMethod": "2CP"
  },
  {
    "id": "eltham",
    "name": "Eltham",
    "region": "North-Eastern Metropolitan",
    "enrolment": 50164,
    "enrolmentVariance": -5.742202179631713,
    "alpTpp2022": 59.004652860140496,
    "marginFromFifty": 9.004652860140496,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "essendon",
    "name": "Essendon",
    "region": "Northern Metropolitan",
    "enrolment": 53259,
    "enrolmentVariance": 0.07328072153324683,
    "alpTpp2022": 62.45013972818688,
    "marginFromFifty": 12.450139728186883,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "eureka",
    "name": "Eureka",
    "region": "Western Victoria",
    "enrolment": 57541,
    "enrolmentVariance": 8.11912814731304,
    "alpTpp2022": 57.17285123875616,
    "marginFromFifty": 7.172851238756159,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "euroa",
    "name": "Euroa",
    "region": "Northern Victoria",
    "enrolment": 52751,
    "enrolmentVariance": -0.8812476512589273,
    "alpTpp2022": 40.06912551489039,
    "marginFromFifty": 9.930874485109612,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "evelyn",
    "name": "Evelyn",
    "region": "Eastern Victoria",
    "enrolment": 52822,
    "enrolmentVariance": -0.7478391582111908,
    "alpTpp2022": 44.78510750349186,
    "marginFromFifty": 5.214892496508142,
    "tppMethod": "2CP"
  },
  {
    "id": "footscray",
    "name": "Footscray",
    "region": "Western Metropolitan",
    "enrolment": 51358,
    "enrolmentVariance": -3.4986847049981225,
    "alpTpp2022": 75.66435299950422,
    "marginFromFifty": 25.664352999504217,
    "tppMethod": "2PP"
  },
  {
    "id": "frankston",
    "name": "Frankston",
    "region": "South-Eastern Metropolitan",
    "enrolment": 50897,
    "enrolmentVariance": -4.364900413378437,
    "alpTpp2022": 58.65902205753486,
    "marginFromFifty": 8.659022057534862,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "geelong",
    "name": "Geelong",
    "region": "Western Victoria",
    "enrolment": 53596,
    "enrolmentVariance": 0.7065013152949905,
    "alpTpp2022": 64.70890487467048,
    "marginFromFifty": 14.70890487467048,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "gippsland-east",
    "name": "Gippsland East",
    "region": "Eastern Victoria",
    "enrolment": 51367,
    "enrolmentVariance": -3.481773769259671,
    "alpTpp2022": 26.077188667644137,
    "marginFromFifty": 23.922811332355863,
    "tppMethod": "2CP"
  },
  {
    "id": "gippsland-south",
    "name": "Gippsland South",
    "region": "Eastern Victoria",
    "enrolment": 50681,
    "enrolmentVariance": -4.770762871101088,
    "alpTpp2022": 34.7502832326284,
    "marginFromFifty": 15.249716767371602,
    "tppMethod": "2CP"
  },
  {
    "id": "glen-waverley",
    "name": "Glen Waverley",
    "region": "North-Eastern Metropolitan",
    "enrolment": 50605,
    "enrolmentVariance": -4.91356632844796,
    "alpTpp2022": 53.30333355721226,
    "marginFromFifty": 3.3033335572122624,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "greenvale",
    "name": "Greenvale",
    "region": "Northern Metropolitan",
    "enrolment": 55119,
    "enrolmentVariance": 3.5682074408117295,
    "alpTpp2022": 56.91938377123562,
    "marginFromFifty": 6.919383771235623,
    "tppMethod": "2CP"
  },
  {
    "id": "hastings",
    "name": "Hastings",
    "region": "Eastern Victoria",
    "enrolment": 50490,
    "enrolmentVariance": -5.12965050732806,
    "alpTpp2022": 51.353317811408616,
    "marginFromFifty": 1.3533178114086155,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "hawthorn",
    "name": "Hawthorn",
    "region": "Southern Metropolitan",
    "enrolment": 51502,
    "enrolmentVariance": -3.2281097331830098,
    "alpTpp2022": 48.25772963213721,
    "marginFromFifty": 1.7422703678627869,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "ivanhoe",
    "name": "Ivanhoe",
    "region": "North-Eastern Metropolitan",
    "enrolment": 49795,
    "enrolmentVariance": -6.435550544907929,
    "alpTpp2022": 62.750314047144016,
    "marginFromFifty": 12.750314047144016,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "kalkallo",
    "name": "Kalkallo",
    "region": "Northern Metropolitan",
    "enrolment": 68679,
    "enrolmentVariance": 29.047350620067665,
    "alpTpp2022": 66.43081369275998,
    "marginFromFifty": 16.430813692759983,
    "tppMethod": "2CP"
  },
  {
    "id": "kew",
    "name": "Kew",
    "region": "Southern Metropolitan",
    "enrolment": 50826,
    "enrolmentVariance": -4.498308906426173,
    "alpTpp2022": 46.024499908240045,
    "marginFromFifty": 3.9755000917599546,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "kororoit",
    "name": "Kororoit",
    "region": "Western Metropolitan",
    "enrolment": 60816,
    "enrolmentVariance": 14.272829763246918,
    "alpTpp2022": 64.24695556500212,
    "marginFromFifty": 14.246955565002125,
    "tppMethod": "2CP"
  },
  {
    "id": "lara",
    "name": "Lara",
    "region": "Western Victoria",
    "enrolment": 51373,
    "enrolmentVariance": -3.470499812100716,
    "alpTpp2022": 66.15310908265671,
    "marginFromFifty": 16.153109082656712,
    "tppMethod": "2CP"
  },
  {
    "id": "laverton",
    "name": "Laverton",
    "region": "Western Metropolitan",
    "enrolment": 55378,
    "enrolmentVariance": 4.0548665915069435,
    "alpTpp2022": 68.01397473797365,
    "marginFromFifty": 18.013974737973655,
    "tppMethod": "2CP"
  },
  {
    "id": "lowan",
    "name": "Lowan",
    "region": "Western Victoria",
    "enrolment": 50877,
    "enrolmentVariance": -4.40248027057496,
    "alpTpp2022": 28.392522932600105,
    "marginFromFifty": 21.607477067399895,
    "tppMethod": "2CP"
  },
  {
    "id": "macedon",
    "name": "Macedon",
    "region": "Northern Victoria",
    "enrolment": 50980,
    "enrolmentVariance": -4.2089440060127705,
    "alpTpp2022": 59.53978215393494,
    "marginFromFifty": 9.539782153934937,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "malvern",
    "name": "Malvern",
    "region": "Southern Metropolitan",
    "enrolment": 48672,
    "enrolmentVariance": -8.5456595264938,
    "alpTpp2022": 41.717791411042946,
    "marginFromFifty": 8.282208588957054,
    "tppMethod": "2CP"
  },
  {
    "id": "melbourne",
    "name": "Melbourne",
    "region": "Northern Metropolitan",
    "enrolment": 56327,
    "enrolmentVariance": 5.838030815482889,
    "alpTpp2022": 75.0135233660246,
    "marginFromFifty": 25.0135233660246,
    "tppMethod": "2PP"
  },
  {
    "id": "melton",
    "name": "Melton",
    "region": "Western Victoria",
    "enrolment": 59471,
    "enrolmentVariance": 11.745584366779404,
    "alpTpp2022": 54.59475265158563,
    "marginFromFifty": 4.59475265158563,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "mildura",
    "name": "Mildura",
    "region": "Northern Victoria",
    "enrolment": 48364,
    "enrolmentVariance": -9.124389327320568,
    "alpTpp2022": 35.88358678552701,
    "marginFromFifty": 14.116413214472992,
    "tppMethod": "2PP"
  },
  {
    "id": "mill-park",
    "name": "Mill Park",
    "region": "North-Eastern Metropolitan",
    "enrolment": 48149,
    "enrolmentVariance": -9.528372792183381,
    "alpTpp2022": 61.43423137876387,
    "marginFromFifty": 11.434231378763869,
    "tppMethod": "2CP"
  },
  {
    "id": "monbulk",
    "name": "Monbulk",
    "region": "Eastern Victoria",
    "enrolment": 49757,
    "enrolmentVariance": -6.506952273581355,
    "alpTpp2022": 57.55436993085629,
    "marginFromFifty": 7.554369930856289,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "mordialloc",
    "name": "Mordialloc",
    "region": "South-Eastern Metropolitan",
    "enrolment": 53763,
    "enrolmentVariance": 1.0202931228861416,
    "alpTpp2022": 58.19469347919834,
    "marginFromFifty": 8.194693479198342,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "mornington",
    "name": "Mornington",
    "region": "Eastern Victoria",
    "enrolment": 49721,
    "enrolmentVariance": -6.574596016535143,
    "alpTpp2022": 41.719366649232086,
    "marginFromFifty": 8.280633350767914,
    "tppMethod": "2PP"
  },
  {
    "id": "morwell",
    "name": "Morwell",
    "region": "Eastern Victoria",
    "enrolment": 55014,
    "enrolmentVariance": 3.370913190529882,
    "alpTpp2022": 45.58378215945078,
    "marginFromFifty": 4.416217840549223,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "mulgrave",
    "name": "Mulgrave",
    "region": "South-Eastern Metropolitan",
    "enrolment": 47783,
    "enrolmentVariance": -10.216084178880118,
    "alpTpp2022": 60.19860088558179,
    "marginFromFifty": 10.19860088558179,
    "tppMethod": "2CP"
  },
  {
    "id": "murray-plains",
    "name": "Murray Plains",
    "region": "Northern Victoria",
    "enrolment": 48198,
    "enrolmentVariance": -9.436302142051863,
    "alpTpp2022": 27.112457477714596,
    "marginFromFifty": 22.887542522285404,
    "tppMethod": "2CP"
  },
  {
    "id": "narracan",
    "name": "Narracan",
    "region": "Eastern Victoria",
    "enrolment": 54562,
    "enrolmentVariance": 2.5216084178880194,
    "alpTpp2022": null,
    "marginFromFifty": null,
    "tppMethod": "Not available"
  },
  {
    "id": "narre-warren-north",
    "name": "Narre Warren North",
    "region": "South-Eastern Metropolitan",
    "enrolment": 53085,
    "enrolmentVariance": -0.25366403607666144,
    "alpTpp2022": 59.16341381138258,
    "marginFromFifty": 9.163413811382583,
    "tppMethod": "2CP"
  },
  {
    "id": "narre-warren-south",
    "name": "Narre Warren South",
    "region": "South-Eastern Metropolitan",
    "enrolment": 56645,
    "enrolmentVariance": 6.435550544907929,
    "alpTpp2022": 58.49576320642406,
    "marginFromFifty": 8.495763206424058,
    "tppMethod": "2CP"
  },
  {
    "id": "nepean",
    "name": "Nepean",
    "region": "Eastern Victoria",
    "enrolment": 51538,
    "enrolmentVariance": -3.1604659902292407,
    "alpTpp2022": 43.317893292159894,
    "marginFromFifty": 6.682106707840106,
    "tppMethod": "2CP"
  },
  {
    "id": "niddrie",
    "name": "Niddrie",
    "region": "Western Metropolitan",
    "enrolment": 52224,
    "enrolmentVariance": -1.871476888387806,
    "alpTpp2022": 56.69475877089153,
    "marginFromFifty": 6.694758770891532,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "northcote",
    "name": "Northcote",
    "region": "Northern Metropolitan",
    "enrolment": 53364,
    "enrolmentVariance": 0.2705749718151128,
    "alpTpp2022": 81.70348482716571,
    "marginFromFifty": 31.70348482716571,
    "tppMethod": "2PP"
  },
  {
    "id": "oakleigh",
    "name": "Oakleigh",
    "region": "Southern Metropolitan",
    "enrolment": 53877,
    "enrolmentVariance": 1.2344983089064225,
    "alpTpp2022": 63.48439990890458,
    "marginFromFifty": 13.484399908904578,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "ovens-valley",
    "name": "Ovens Valley",
    "region": "Northern Victoria",
    "enrolment": 49293,
    "enrolmentVariance": -7.378804960541147,
    "alpTpp2022": 32.03391506402333,
    "marginFromFifty": 17.966084935976667,
    "tppMethod": "2CP"
  },
  {
    "id": "pakenham",
    "name": "Pakenham",
    "region": "Eastern Victoria",
    "enrolment": 54881,
    "enrolmentVariance": 3.12100714017286,
    "alpTpp2022": 50.39493657858852,
    "marginFromFifty": 0.3949365785885206,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "pascoe-vale",
    "name": "Pascoe Vale",
    "region": "Northern Metropolitan",
    "enrolment": 51700,
    "enrolmentVariance": -2.856069146937243,
    "alpTpp2022": 72.246914806446,
    "marginFromFifty": 22.246914806446,
    "tppMethod": "2PP"
  },
  {
    "id": "point-cook",
    "name": "Point Cook",
    "region": "Western Metropolitan",
    "enrolment": 55088,
    "enrolmentVariance": 3.5099586621570777,
    "alpTpp2022": 58.33908795621371,
    "marginFromFifty": 8.33908795621371,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "polwarth",
    "name": "Polwarth",
    "region": "Western Victoria",
    "enrolment": 54763,
    "enrolmentVariance": 2.8992859827132635,
    "alpTpp2022": 48.21312116864484,
    "marginFromFifty": 1.7868788313551605,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "prahran",
    "name": "Prahran",
    "region": "Southern Metropolitan",
    "enrolment": 49193,
    "enrolmentVariance": -7.566704246523877,
    "alpTpp2022": 61.070764212725834,
    "marginFromFifty": 11.070764212725834,
    "tppMethod": "2PP"
  },
  {
    "id": "preston",
    "name": "Preston",
    "region": "Northern Metropolitan",
    "enrolment": 53194,
    "enrolmentVariance": -0.04885381435549789,
    "alpTpp2022": 69.67157588378453,
    "marginFromFifty": 19.671575883784527,
    "tppMethod": "2PP"
  },
  {
    "id": "richmond",
    "name": "Richmond",
    "region": "Northern Metropolitan",
    "enrolment": 49523,
    "enrolmentVariance": -6.946636602780909,
    "alpTpp2022": 74.12599733205809,
    "marginFromFifty": 24.12599733205809,
    "tppMethod": "2PP"
  },
  {
    "id": "ringwood",
    "name": "Ringwood",
    "region": "North-Eastern Metropolitan",
    "enrolment": 54473,
    "enrolmentVariance": 2.3543780533633982,
    "alpTpp2022": 57.53065372762441,
    "marginFromFifty": 7.530653727624411,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "ripon",
    "name": "Ripon",
    "region": "Western Victoria",
    "enrolment": 54114,
    "enrolmentVariance": 1.679819616685454,
    "alpTpp2022": 52.99355234878723,
    "marginFromFifty": 2.993552348787233,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "rowville",
    "name": "Rowville",
    "region": "South-Eastern Metropolitan",
    "enrolment": 50344,
    "enrolmentVariance": -5.403983464862831,
    "alpTpp2022": 46.33493970347483,
    "marginFromFifty": 3.6650602965251693,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "sandringham",
    "name": "Sandringham",
    "region": "Southern Metropolitan",
    "enrolment": 49299,
    "enrolmentVariance": -7.367531003382192,
    "alpTpp2022": 44.850424719931056,
    "marginFromFifty": 5.1495752800689445,
    "tppMethod": "2CP"
  },
  {
    "id": "shepparton",
    "name": "Shepparton",
    "region": "Northern Victoria",
    "enrolment": 52325,
    "enrolmentVariance": -1.681698609545274,
    "alpTpp2022": 25.65797438318685,
    "marginFromFifty": 24.34202561681315,
    "tppMethod": "2PP"
  },
  {
    "id": "south-barwon",
    "name": "South Barwon",
    "region": "Western Victoria",
    "enrolment": 60309,
    "enrolmentVariance": 13.320180383314545,
    "alpTpp2022": 59.79992917847026,
    "marginFromFifty": 9.799929178470258,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "south-west-coast",
    "name": "South-West Coast",
    "region": "Western Victoria",
    "enrolment": 54209,
    "enrolmentVariance": 1.8583239383690489,
    "alpTpp2022": 41.95094074204326,
    "marginFromFifty": 8.049059257956742,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "st-albans",
    "name": "St Albans",
    "region": "Western Metropolitan",
    "enrolment": 47610,
    "enrolmentVariance": -10.541149943630208,
    "alpTpp2022": 59.564340911636236,
    "marginFromFifty": 9.564340911636236,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "sunbury",
    "name": "Sunbury",
    "region": "Western Metropolitan",
    "enrolment": 51005,
    "enrolmentVariance": -4.161969184517111,
    "alpTpp2022": 56.412772503049915,
    "marginFromFifty": 6.412772503049915,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "sydenham",
    "name": "Sydenham",
    "region": "Western Metropolitan",
    "enrolment": 63850,
    "enrolmentVariance": 19.97369409996241,
    "alpTpp2022": 58.7275879374059,
    "marginFromFifty": 8.7275879374059,
    "tppMethod": "2CP"
  },
  {
    "id": "tarneit",
    "name": "Tarneit",
    "region": "Western Metropolitan",
    "enrolment": 59482,
    "enrolmentVariance": 11.766253288237513,
    "alpTpp2022": 62.577802822673604,
    "marginFromFifty": 12.577802822673604,
    "tppMethod": "2CP"
  },
  {
    "id": "thomastown",
    "name": "Thomastown",
    "region": "Northern Metropolitan",
    "enrolment": 55351,
    "enrolmentVariance": 4.004133784291626,
    "alpTpp2022": 65.99577121751466,
    "marginFromFifty": 15.995771217514658,
    "tppMethod": "2CP"
  },
  {
    "id": "warrandyte",
    "name": "Warrandyte",
    "region": "North-Eastern Metropolitan",
    "enrolment": 51699,
    "enrolmentVariance": -2.857948139797063,
    "alpTpp2022": 45.84996009577015,
    "marginFromFifty": 4.15003990422985,
    "tppMethod": "2CP"
  },
  {
    "id": "wendouree",
    "name": "Wendouree",
    "region": "Western Victoria",
    "enrolment": 53148,
    "enrolmentVariance": -0.1352874859075564,
    "alpTpp2022": 63.46122024442711,
    "marginFromFifty": 13.46122024442711,
    "tppMethod": "2CP"
  },
  {
    "id": "werribee",
    "name": "Werribee",
    "region": "Western Metropolitan",
    "enrolment": 61589,
    "enrolmentVariance": 15.725291243893261,
    "alpTpp2022": 60.5012417008768,
    "marginFromFifty": 10.501241700876797,
    "tppMethod": "2CP"
  },
  {
    "id": "williamstown",
    "name": "Williamstown",
    "region": "Western Metropolitan",
    "enrolment": 49909,
    "enrolmentVariance": -6.221345358887629,
    "alpTpp2022": 63.44229486324217,
    "marginFromFifty": 13.442294863242168,
    "tppMethod": "Preference distribution"
  },
  {
    "id": "yan-yean",
    "name": "Yan Yean",
    "region": "Northern Victoria",
    "enrolment": 56321,
    "enrolmentVariance": 5.826756858323933,
    "alpTpp2022": 54.45046047970853,
    "marginFromFifty": 4.450460479708532,
    "tppMethod": "2CP"
  }
] as const;

export const validationFolds = [
  {
    "cycle": "2010",
    "districts": 88,
    "baselineMae": 2.538152571009978,
    "candidateMae": 2.5820883188576973,
    "baselineRmse": 3.3400949899643066,
    "candidateRmse": 3.4659802502591375,
    "baselineWinnerErrors": 5,
    "candidateWinnerErrors": 8
  },
  {
    "cycle": "2014",
    "districts": 88,
    "baselineMae": 2.2526151360626647,
    "candidateMae": 2.2029180036153098,
    "baselineRmse": 3.01901631974918,
    "candidateRmse": 2.9590336306996785,
    "baselineWinnerErrors": 2,
    "candidateWinnerErrors": 1
  },
  {
    "cycle": "2018",
    "districts": 87,
    "baselineMae": 2.9906564987292357,
    "candidateMae": 3.0031620484178685,
    "baselineRmse": 3.8284463607680315,
    "candidateRmse": 3.8889251521142776,
    "baselineWinnerErrors": 7,
    "candidateWinnerErrors": 7
  },
  {
    "cycle": "2022",
    "districts": 77,
    "baselineMae": 3.423065272441428,
    "candidateMae": 3.5551473110983745,
    "baselineRmse": 4.52972047834986,
    "candidateRmse": 4.499669143435017,
    "baselineWinnerErrors": 7,
    "candidateWinnerErrors": 8
  }
] as const;
