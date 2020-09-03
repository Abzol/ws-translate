# ws-translate
translates card games

usage:

    $python3 weiss.py <source>

where `source` is either a single file, or a directory containing a group of files.
Files must be correctly named with their official Weiß Schwarz card number (found in the lower left corner of all cards).
If you're using an operating system that doesn't allow slashes in file names (that is, most of them), please replace all slashes with underscores.

As an example, *Serval, Curious About Everything* is card no. **KMN/W51-001** and as such the source file should be `KMN_W51-001.jpg`.
For best results, the rarity symbol (including *TD* rarity) should not be included. (Note that trial deck cards *should* retain the T prefix on their card numbers).

## Usage notes and thanks

Thanks to [Heart of the Cards](https://heartofthecards.com/), whom I source the translations from.
Thanks to [Little Akiba](https://littleakiba.com), whom I routinely use to source JP card scans.
Thanks to [JKTCG](https://jktcg.com), whom I routinely use to source English card scans. (You should play EN Weiß. It's a good game.)