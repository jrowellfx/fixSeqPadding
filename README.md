# fixSeqPadding

Cmd-line util to repair badly-padded frames in image-sequences.
You'll probably never need this util, it only exists as a helper for users of `lsseq`
(and `renumseq`),

`lsseq` reports when sequences have badly padded frames, so in the rare
situation that you stumble upon a badly-padded frame-sequence, this might save you some time
as opposed to cobbling together a shell script to fix the bad-filenames. (Or worse
renaming each one by hand in a file-explorer - ouch!)

