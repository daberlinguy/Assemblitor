import os
import glob as gl
import pathlib as pl
from ast import literal_eval

#          Copyright Blyfh https://github.com/Blyfh
# Distributed under the Boost Software License, Version 1.0.
#     (See accompanying file LICENSE_1_0.txt or copy at
#           http://www.boost.org/LICENSE_1_0.txt)


program_dir = pl.Path(__file__).parent.parent.absolute()


class PackHandler:
    
    def gt_pack_data(self, pack, path):
        # literal_eval safely evaluates literal structures, here a dict
        return dict(literal_eval(self.gt_pack_str(pack, path)))
    
    def gt_pack_str(self, pack, path):
        try:
            with open(f"{path}/{pack}.dict", "r", encoding="utf-8") as file:
                return file.read()
        except:
            raise FileNotFoundError(f"Couldn't fetch pack '{pack}' from directory '{path}'.")
    
    def st_pack_data(self, pack, dir, new_data):
        try:
            with open(f"{dir}/{pack}.dict", "w", encoding="utf-8") as file:
                file.write(self.format(new_data))
        except:
            raise FileNotFoundError(f"Couldn't update pack '{pack}' from directory '{dir}'.")
    
    def format(self, dict_data, depth=1):
        items_str = ""
        for key, value in dict_data.items():
            if type(value) is dict:
                items_str += "    " * depth + f"\"{key}\": {self.format(value, depth + 1)},\n"
            else:
                items_str += "    " * depth + f"\"{key}\": {self.format_no_dict_value(value)},\n"
        return "{" + f"\n{items_str[:-2]}\n" + "    " * (depth - 1) + "}"
    
    def format_no_dict_value(self, value):
        if type(value) is str:
            if len(value.split("\n")) > 1:
                value = f"\"\"\"{value}\"\"\""
            else:
                value = f"\"{value}\""
        elif type(value) is tuple or type(value) is list:
            elements_str = ""
            for element in value:
                if type(element) is str:
                    elements_str += f"\"{element}\", "
                else:
                    elements_str += str(element) + ", "
            if type(value) is tuple:
                value = f"({elements_str[:-2]})"
            else:
                value = f"[{elements_str[:-2]}]"
        return value

class ProfileHandler:
    
    def __init__(self, profile_dir):
        self.profile_dir = profile_dir
        self.default_profile_data = ph.gt_pack_data("default_profile", f"{program_dir}/resources")
    
    def reset_profile(self):
        default_profile_data = ph.gt_pack_data("default_profile", f"{program_dir}/resources")
        ph.st_pack_data("profile", f"{self.profile_dir}", new_data=default_profile_data)
    
    def save_profile_data(self, key, new_value):
        profile_data = self.gt_profile_data()
        try:
            profile_data[key] = new_value
        except:
            raise FileNotFoundError(f"Couldn't fetch profile data for '{key}'.")
        ph.st_pack_data("profile", f"{self.profile_dir}", new_data=profile_data)
    
    def gt_profile_data(self):
        try:
            return ph.gt_pack_data("profile", f"{self.profile_dir}")
        except FileNotFoundError:
            self.reset_profile()
            return ph.gt_pack_data("profile", f"{self.profile_dir}")

    def gt_value(self, key):
        profile_data = self.gt_profile_data()
        if key in profile_data:
            return profile_data[key]
        if key in self.default_profile_data:
            return self.default_profile_data[key]
        if key == "auto_shift_addresses":
            return False
        raise FileNotFoundError(f"Couldn't fetch profile data for '{key}'.")
    
    def theme(self):
        theme = self.gt_value("theme")
        if theme == "dark" or theme == "light":
            return theme
        else:
            raise RuntimeError(f"Unknown theme '{theme}' in profile.")
    
    def language(self):
        return self.gt_value("language")
    
    def code_font_face(self):
        return self.gt_value("code_font_face")
    
    def code_font_size(self):
        return self.gt_value("code_font_size")
    
    def code_font(self):
        return self.code_font_face(), self.code_font_size()
    
    def min_adr_len(self):
        return self.gt_value("min_adr_len")
    
    def max_cels(self):
        return self.gt_value("max_cels")
    
    def max_jmps(self):
        return self.gt_value("max_jmps")
    
    def closing_unsaved(self):
        return self.gt_value("closing_unsaved")
    
    def auto_shift_addresses(self):
        return self.gt_value("auto_shift_addresses")
    
    def dev_mode(self):
        return self.gt_value("dev_mode")

    def colors(self, theme=None):
        theme = theme if theme else self.theme()
        profile_data = self.gt_profile_data()
        profile_colors = profile_data.get("colors", {})
        default_colors = self.default_profile_data.get("colors", {})
        base_palette = default_colors.get(theme, {}).copy() if default_colors.get(theme) else {}
        base_palette.update(profile_colors.get(theme, {}))
        if not base_palette:
            raise FileNotFoundError(f"Couldn't fetch color data for theme '{theme}'.")
        return base_palette

    def save_theme_colors(self, theme, new_palette: dict):
        profile_data = self.gt_profile_data()
        colors = profile_data.get("colors", {})
        colors[theme] = new_palette
        profile_data["colors"] = colors
        ph.st_pack_data("profile", f"{self.profile_dir}", new_data=profile_data)


class LangHandler:
    
    def __init__(self, cur_lang="en_US"):
        self.cur_lang = cur_lang
        self.cur_lang_data = ph.gt_pack_data(self.cur_lang, f"{program_dir}/languages")
    
    def gt_langs(self):
        lang_paths = gl.glob(os.path.join(program_dir, "languages/*.dict"))
        langs = []
        for lang_path in lang_paths:
            langs.append(os.path.basename(lang_path).split(".dict")[0])
        return langs
    
    def gt_lang(self, lang_name):
        langs = self.gt_langs()
        for lang in langs:
            if self.gt_lang_name(lang) == lang_name:
                return lang
        raise FileNotFoundError(f"Couldn't fetch language ID for '{lang_name}'.")
    
    def gt_lang_name(self, lang):
        lang_data = ph.gt_pack_data(lang, f"{program_dir}/languages")
        try:
            lang_name = lang_data["info"]["name"]
        except:
            raise FileNotFoundError(f"Couldn't fetch info data for 'name' from language pack '{lang}'.")
        return lang_name
    
    def gt_langs_with_names(self):
        langs_with_names = {}
        for lang in self.gt_langs():
            langs_with_names[lang] = self.gt_lang_name(lang)
        return langs_with_names
    
    def demo(self):
        try:
            demo = self.cur_lang_data["demo"]
        except:
            raise FileNotFoundError(f"Couldn't fetch demo data from language pack '{self.cur_lang}'.")
        return demo
    
    def opt_win(self, key):
        try:
            ele = self.cur_lang_data["opt_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'options' window data for '{key}' from language pack "
                                    f"'{self.cur_lang}'.")
        return ele
    
    def abt_win(self, key):
        try:
            ele = self.cur_lang_data["abt_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'about' window data for '{key}' from language pack "
                                    f"'{self.cur_lang}'.")
        return ele
    
    def shc_win(self, key):
        try:
            ele = self.cur_lang_data["shc_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'shortcuts' window data for '{key}' from language pack "
                                    f"'{self.cur_lang}'.")
        return ele
    
    def gui(self, key):
        try:
            ele = self.cur_lang_data["gui"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch gui data for '{key}' from language pack '{self.cur_lang}'.")
        return ele
    
    def file_mng(self, key):
        try:
            ele = self.cur_lang_data["file_mng"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch file_mng data for '{key}' from language pack '{self.cur_lang}'.")
        return ele
    
    def asm_win(self, key):
        try:
            ele = self.cur_lang_data["asm_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'Assembly' window data for '{key}' from language pack "
                                    f"'{self.cur_lang}'.")
        if key == "text":
            text_code_pairs = []
            blocks = ele.split("}")
            if len(blocks) == 1:
                text_code_pairs = [(blocks[0], "")]
            else:
                for i in range(len(blocks) - 1):
                    text_code_pair = blocks[i].split("{", maxsplit = 1)
                    if len(text_code_pair) == 1:
                        raise SyntaxError(f"Unmatched curly bracket in 'Assembly' window data for 'text' from language "
                                          f"pack '{self.cur_lang}'.")
                    else:
                        text_code_pairs.append(text_code_pair)
                text_code_pairs.append((blocks[len(blocks) - 1], ""))
            return text_code_pairs
        return ele

class ErrorHandler:
    
    def __init__(self):
        pack_data = ph.gt_pack_data("errors", f"{program_dir}/resources")
        self.errors = pack_data["errors"]
        self.messages = pack_data["messages"]
    
    def error(self, err, **kwargs):
        try:
            err_tpl = self.errors[err]
        except:
            raise FileNotFoundError(f"Couldn't fetch error data for '{err}'.")
        err_name = err_tpl[0]
        err_desc = ""
        blocks = err_tpl[1].split("}")
        if len(blocks) == 1:
            err_desc = blocks[0]
        else:
            for i in range(len(blocks) - 1):
                txt_arg_pair = blocks[i].split("{", maxsplit = 1)
                if len(txt_arg_pair) == 1:
                    raise SyntaxError(f"Unmatched curly bracket in error data for '{err}'.")
                else:
                    arg = None
                    for kw in kwargs: # search for matching argument
                        if kw == txt_arg_pair[1]:
                            arg = kwargs[kw]
                    if arg is None:
                        raise TypeError(f"LangHandler.error() missing required keyword argument '{txt_arg_pair[1]}' in "
                                        f"error data for '{err}'.")
                    err_desc += txt_arg_pair[0] + str(arg)
            err_desc += blocks[len(blocks) - 1]
        return err_name + ": " + err_desc
    
    def prg_state_msg(self):
        try:
            prg_state_msg = self.messages["PrgStateMsg"]
        except:
            raise FileNotFoundError(f"Couldn't fetch error message data for 'PrgStateMsg'.")
        return prg_state_msg


ph = PackHandler()
