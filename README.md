# cachepreloader
Cache Preloader is a free software that crawls a website to generate its cache. Its helps search engines bots (google bot) to read your website.

This software is no longer supported.

By Nicolas Lorenzon from http://www.lorenzon.ovh

## How to use

Cache Preloader is a free software that crawls a website to generate its cache. Its helps search engines bots (google bot) to read your website.

But your main benefits is that your website (e-commerce, journal, blog) is faster (really faster).

For a maximum efficacity you need to run Cache Preloader after a modification on your content (new article, template change, empty cache, etc).

Cache Preloader is free with no warranty. It may damage your computer (even if that would be very surprising and our test haven't revealed that bug).

The first thing you need to do is enter your webite url (whith "http://", exemple : http://www.my-website.com).

After that you can directly push the "Preload Cache" button to start generating the cache. If you want to stop the process you can hit the "Stop cache preloading" button or just push "Quit".

There is an optional parameter : you can set an exception list ("Do not crawl url with"). If a word of this list (comma separated) is in the url, the cache won't be created.

## Custom configuration

You can store your own configuration for faster setup.

Create a file named config.cfg in the same directory than CachePreloader.exe.

Add these lines to the file :

SITE=http://www.my-wordpress.com

CONFIG=.img, .png, .gif, .jpeg, .jpg, /tag/, /author/, /comment-subscriptions, /wp-login, /wp-admin, /feed/, /wp-content/, /trackback/, /archives/


----------------------------
  * SITE : your website url
  * CONFIG : your exception list

