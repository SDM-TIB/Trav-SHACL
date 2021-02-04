package unibz.shapes.util;

import java.util.Iterator;
import java.util.Spliterator;
import java.util.Spliterators;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

public class StreamUt {

    public  static <T> Stream<T> toStream(Iterator<T> it){
         Spliterator<T> spliterator = Spliterators.spliteratorUnknownSize(it, 0);
        return StreamSupport.stream(spliterator, false);
    }
}
