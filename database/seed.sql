INSERT INTO movies(title,genre,rating,description,cast,duration,language,poster_url,release_date) VALUES
('Skyline Protocol','Action, Thriller',8.4,'A cybercrime investigator races across Jaipur to stop a coordinated attack.','Arjun Mehta, Rhea Kapoor',142,'Hindi','https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=700&q=80','2026-08-14'),
('Midnight Café','Drama, Romance',8.1,'Two strangers reconnect during a long night at a neighbourhood café.','Mira Sen, Kabir Rao',126,'Hindi','https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=700&q=80','2026-09-04'),
('Orbit 9','Sci-Fi, Adventure',8.7,'A crew discovers a signal that changes everything they know about Mars.','Ishaan Verma, Tara Shah',148,'English','https://images.unsplash.com/photo-1440404653325-ab127d49abc1?auto=format&fit=crop&w=700&q=80','2026-09-11'),
('Laughing Matters','Comedy',7.6,'A wedding planner gets trapped in the one event she cannot control.','Neel Joshi, Sana Khan',118,'Hindi','https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=700&q=80','2026-08-29'),
('The Last Signal','Horror, Thriller',7.9,'An abandoned radio station starts broadcasting tomorrow’s headlines.','Aanya Singh, Dev Malhotra',109,'Hindi','https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=700&q=80','2026-09-18'),
('Courtyard Stories','Family, Drama',8.0,'Three generations meet under one Jaipur roof and revisit old promises.','Vikram Bedi, Naina Arora',131,'Hindi','https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?auto=format&fit=crop&w=700&q=80','2026-08-22')
ON CONFLICT DO NOTHING;

INSERT INTO theatres(name,location,latitude,longitude,city) VALUES
('PVR Cinemas - World Trade Park','Malviya Nagar, Jaipur',26.8538,75.8045,'Jaipur'),
('INOX - GT Central','JLN Marg, Jaipur',26.8422,75.8062,'Jaipur'),
('Cinepolis - Triton Mega Mall','Jhotwara, Jaipur',26.9600,75.7523,'Jaipur'),
('Raj Mandir Cinema','C-Scheme, Jaipur',26.9124,75.7873,'Jaipur')
ON CONFLICT DO NOTHING;
