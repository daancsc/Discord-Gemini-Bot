
## Popular Movies API

**Endpoint:**  
`GET https://api.themoviedb.org/3/movie/popular`

### Description
This endpoint retrieves a list of movies ordered by popularity.

### Equivalent Discover Call

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc' \
     --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNzc1YzYxYTAzZThlMzIyMDdlY2I2ZjUwNzdiZjE5YyIsIm5iZiI6MTc0NDcxNDAzMy45NCwic3ViIjoiNjdmZTM5MzE3YzI5YWU1YmMzZDk5NmUwIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.XYObLw1Df8n4K8egAULBqDAc82LRcOM-nME6wwXU_yA' \
     --header 'accept: application/json'
```

---

### Query Parameters

- **language** (`string`): Defaults to `en-US`  
- **page** (`int32`): Defaults to `1`  
- **region** (`string`): ISO-3166-1 country code

---

### Response

#### Status Code: 200

#### Response Body

```json
{
  "page": 1,
  "results": [
    {
      "adult": false,
      "backdrop_path": "/path/to/image.jpg",
      "genre_ids": [28, 12],
      "id": 12345,
      "original_language": "en",
      "original_title": "Movie Title",
      "overview": "A short description of the movie.",
      "popularity": 10.5,
      "poster_path": "/path/to/poster.jpg",
      "release_date": "2025-04-21",
      "title": "Movie Title",
      "video": false,
      "vote_average": 7.8,
      "vote_count": 1500
    }
  ],
  "total_pages": 50,
  "total_results": 1000
}
```

---

### Field Descriptions

- **page**: Integer - The current page of results.
- **results**: Array of movie objects, each containing:
  - **adult**: Boolean - Whether the movie is for adults only.
  - **backdrop_path**: String - Path to the backdrop image.
  - **genre_ids**: Array of integers - Genre identifiers.
  - **id**: Integer - The movie's unique identifier.
  - **original_language**: String - The movie's original language.
  - **original_title**: String - The original title of the movie.
  - **overview**: String - A brief description of the movie.
  - **popularity**: Number - The movie's popularity score.
  - **poster_path**: String - Path to the poster image.
  - **release_date**: String - The release date of the movie.
  - **title**: String - The movie's title.
  - **video**: Boolean - Whether the movie has a video available.
  - **vote_average**: Number - The average vote score.
  - **vote_count**: Integer - The number of votes.
- **total_pages**: Integer - The total number of pages available.
- **total_results**: Integer - The total number of results.


---

## Top Rated Movies API

**Endpoint:**  
`GET https://api.themoviedb.org/3/movie/top_rated`

### Description
This endpoint retrieves a list of movies ordered by their rating.

---

### Equivalent Discover Call

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=vote_average.desc&without_genres=99,10755&vote_count.gte=200' \
     --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNzc1YzYxYTAzZThlMzIyMDdlY2I2ZjUwNzdiZjE5YyIsIm5iZiI6MTc0NDcxNDAzMy45NCwic3ViIjoiNjdmZTM5MzE3YzI5YWU1YmMzZDk5NmUwIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.XYObLw1Df8n4K8egAULBqDAc82LRcOM-nME6wwXU_yA' \
     --header 'accept: application/json'
```

---

### Query Parameters

- **language** (`string`): Defaults to `en-US`  
- **page** (`int32`): Defaults to `1`  
- **region** (`string`): ISO-3166-1 country code

---

### Response

#### Status Code: 200

#### Response Body

```json
{
  "page": 1,
  "results": [
    {
      "adult": false,
      "backdrop_path": "/path/to/image.jpg",
      "genre_ids": [28, 12],
      "id": 67890,
      "original_language": "en",
      "original_title": "Top Rated Movie Title",
      "overview": "A short description of the top-rated movie.",
      "popularity": 15.7,
      "poster_path": "/path/to/poster.jpg",
      "release_date": "2025-04-21",
      "title": "Top Rated Movie Title",
      "video": false,
      "vote_average": 9.2,
      "vote_count": 3000
    }
  ],
  "total_pages": 50,
  "total_results": 1000
}
```

---

### Field Descriptions

- **page**: Integer - The current page of results.
- **results**: Array of movie objects, each containing:
  - **adult**: Boolean - Whether the movie is for adults only.
  - **backdrop_path**: String - Path to the backdrop image.
  - **genre_ids**: Array of integers - Genre identifiers.
  - **id**: Integer - The movie's unique identifier.
  - **original_language**: String - The movie's original language.
  - **original_title**: String - The original title of the movie.
  - **overview**: String - A brief description of the movie.
  - **popularity**: Number - The movie's popularity score.
  - **poster_path**: String - Path to the poster image.
  - **release_date**: String - The release date of the movie.
  - **title**: String - The movie's title.
  - **video**: Boolean - Whether the movie has a video available.
  - **vote_average**: Number - The average vote score.
  - **vote_count**: Integer - The number of votes.
- **total_pages**: Integer - The total number of pages available.
- **total_results**: Integer - The total number of results.

---

## Upcoming Movies API

**Endpoint:**  
`GET https://api.themoviedb.org/3/movie/upcoming`

### Description
This endpoint retrieves a list of movies that are being released soon.

---

### Equivalent Discover Call

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&with_release_type=2|3&release_date.gte={min_date}&release_date.lte={max_date}' \
     --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNzc1YzYxYTAzZThlMzIyMDdlY2I2ZjUwNzdiZjE5YyIsIm5iZiI6MTc0NDcxNDAzMy45NCwic3ViIjoiNjdmZTM5MzE3YzI5YWU1YmMzZDk5NmUwIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.XYObLw1Df8n4K8egAULBqDAc82LRcOM-nME6wwXU_yA' \
     --header 'accept: application/json'
```

---

### Query Parameters

- **language** (`string`): Defaults to `en-US`  
- **page** (`int32`): Defaults to `1`  
- **region** (`string`): ISO-3166-1 country code

---

### Response

#### Status Code: 200

#### Response Body

```json
{
  "dates": {
    "maximum": "2025-05-01",
    "minimum": "2025-04-01"
  },
  "page": 1,
  "results": [
    {
      "adult": false,
      "backdrop_path": "/path/to/image.jpg",
      "genre_ids": [28, 12],
      "id": 12345,
      "original_language": "en",
      "original_title": "Upcoming Movie Title",
      "overview": "A short description of an upcoming movie.",
      "popularity": 10.5,
      "poster_path": "/path/to/poster.jpg",
      "release_date": "2025-04-25",
      "title": "Upcoming Movie Title",
      "video": false,
      "vote_average": 8,
      "vote_count": 500
    }
  ],
  "total_pages": 50,
  "total_results": 1000
}
```

---

### Field Descriptions

- **dates**: Object containing:
  - **maximum**: String - The latest date for upcoming movie releases.
  - **minimum**: String - The earliest date for upcoming movie releases.
- **page**: Integer - The current page of results.
- **results**: Array of movie objects, each containing:
  - **adult**: Boolean - Whether the movie is for adults only.
  - **backdrop_path**: String - Path to the backdrop image.
  - **genre_ids**: Array of integers - Genre identifiers.
  - **id**: Integer - The movie's unique identifier.
  - **original_language**: String - The movie's original language.
  - **original_title**: String - The original title of the movie.
  - **overview**: String - A brief description of the movie.
  - **popularity**: Number - The movie's popularity score.
  - **poster_path**: String - Path to the poster image.
  - **release_date**: String - The release date of the movie.
  - **title**: String - The movie's title.
  - **video**: Boolean - Whether the movie has a video available.
  - **vote_average**: Integer - The average vote score.
  - **vote_count**: Integer - The number of votes.
- **total_pages**: Integer - The total number of pages available.
- **total_results**: Integer - The total number of results.

---

## Now Playing Movies API

**Endpoint:**  
`GET https://api.themoviedb.org/3/movie/now_playing`

### Description
This endpoint retrieves a list of movies that are currently playing in theaters.

---

### Recent Requests

| Time | Status | User Agent |
| ---- | ------ | ---------- |
| Make a request to see history. | 0 Requests This Month | See All Requests |

---

### 📘 Note
This call is essentially a "discover" call behind the scenes. If you would like to adjust any of the default filters, head over to the [Discover API](https://www.themoviedb.org/documentation/api).

---

### Equivalent Discover Call

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&with_release_type=2|3&release_date.gte={min_date}&release_date.lte={max_date}' \
     --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNzc1YzYxYTAzZThlMzIyMDdlY2I2ZjUwNzdiZjE5YyIsIm5iZiI6MTc0NDcxNDAzMy45NCwic3ViIjoiNjdmZTM5MzE3YzI5YWU1YmMzZDk5NmUwIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.XYObLw1Df8n4K8egAULBqDAc82LRcOM-nME6wwXU_yA' \
     --header 'accept: application/json'
```

---

### Query Parameters

- **language** (`string`): Defaults to `en-US`  
- **page** (`int32`): Defaults to `1`  
- **region** (`string`): ISO-3166-1 country code

---

### Response

#### Status Code: 200

#### Response Body

```json
{
  "dates": {
    "maximum": "2025-05-01",
    "minimum": "2025-04-01"
  },
  "page": 1,
  "results": [
    {
      "adult": false,
      "backdrop_path": "/path/to/image.jpg",
      "genre_ids": [28, 12],
      "id": 12345,
      "original_language": "en",
      "original_title": "Now Playing Movie Title",
      "overview": "A brief description of a movie currently playing.",
      "popularity": 15.7,
      "poster_path": "/path/to/poster.jpg",
      "release_date": "2025-04-20",
      "title": "Now Playing Movie Title",
      "video": false,
      "vote_average": 8.5,
      "vote_count": 1200
    }
  ],
  "total_pages": 50,
  "total_results": 1000
}
```

---

### Field Descriptions

- **dates**: Object containing:
  - **maximum**: String - The latest date for currently playing movie releases.
  - **minimum**: String - The earliest date for currently playing movie releases.
- **page**: Integer - The current page of results.
- **results**: Array of movie objects, each containing:
  - **adult**: Boolean - Whether the movie is for adults only.
  - **backdrop_path**: String - Path to the backdrop image.
  - **genre_ids**: Array of integers - Genre identifiers.
  - **id**: Integer - The movie's unique identifier.
  - **original_language**: String - The movie's original language.
  - **original_title**: String - The original title of the movie.
  - **overview**: String - A brief description of the movie.
  - **popularity**: Number - The movie's popularity score.
  - **poster_path**: String - Path to the poster image.
  - **release_date**: String - The release date of the movie.
  - **title**: String - The movie's title.
  - **video**: Boolean - Whether the movie has a video available.
  - **vote_average**: Number - The average vote score.
  - **vote_count**: Integer - The number of votes.
- **total_pages**: Integer - The total number of pages available.
- **total_results**: Integer - The total number of results.