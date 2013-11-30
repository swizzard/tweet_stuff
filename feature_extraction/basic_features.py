def get_tweet_features(parsed_tweet, other_features=None, other_user_features=None):
    to_extract = {"hashtags":None, "text":None ,"unshortened_urls":[hash] ,"url_domains":[hash],
    "user":[get_user_features], "created_at":None, "mentions":None, "id":None}
    final_features = {}
    if other_features:
        to_extract.update(other_features)
    if other_user_features:
        to_extract["user"].append(other_user_features)
    for k in to_extract.keys():
        feat = parsed_tweet.get(k)
        func = to_extract[k]
        if func:
            if type(feat) == list:
                mapped = []
                for x in feat:
                    mapped.append(func[0](x, *func[1:])
                feat = mapped
            else:
                feat = func[0](feat, *func[1:])
        final_features[k] = feat
    return final_features

def get_user_features(parsed_user, other_features=None):
    to_extract = {"created_at":None, "followers_count":None, "following_count":None, "lang":None,
    "location":None, "id":None, "utc_tz":None, "statuses_count":None}
    final_features = {}
    if other_features:
        to_extract.update(other_features)
    for k in to_extract.keys():
        feat = parsed_tweet.get(k)
        func = to_extract[k]
        if func:
            if type(feat) == list:
                mapped = []
                for x in feat:
                    mapped.append(func[0](x,*func[1:])
                feat = mapped
            else:
                feat = func[0](feat, *func[1:])
        final_features[k] = feat
    return final_features
